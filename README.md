# Semantic Document Search Engine

Ask questions about PDF and Word files. The API retrieves passages with hybrid lexical and vector search, reranks them, and asks Amazon Bedrock for an answer that cites the source document and, when available, the page or section.

The same Python code runs on macOS and Windows. Docker Compose is the setup that does not depend on a host database install.

## Architecture

```text
PDF / DOCX
    -> text extraction (page for PDF, heading and tables for Word)
    -> overlapping chunks
    -> Amazon Bedrock embeddings
    -> PostgreSQL (pgvector + full-text index)

Question
    -> query cleanup
    -> lexical candidates (PostgreSQL full text, rescored with Okapi BM25)
    -> vector candidates (pgvector cosine)
    -> reciprocal rank fusion
    -> reranking
    -> Amazon Bedrock answer
    -> answer plus citations
```

Retrieval, reranking, embeddings, and generation are separate services behind small interfaces in `backend/app/services`. The default reranker is local and does not call Bedrock. Set `BEDROCK_RERANK_MODEL` when you want Bedrock to rerank instead.

Lexical search is not a claim that PostgreSQL's built-in ranker is Okapi BM25. Full-text search selects the candidate pool and orders it with `ts_rank_cd`. Okapi BM25 (`k1 = 1.5`, `b = 0.75`) then rescores that pool. Vector search is cosine distance on a 1024-dimension embedding column.

## What you need

- Docker Desktop on Windows or Docker Engine on macOS
- An AWS account with Amazon Bedrock model access for the embedding model and the chat model you set in `.env`
- Optional: a Bedrock rerank model, if you set `BEDROCK_RERANK_MODEL`

The database vector column is fixed at 1024 dimensions, which matches Amazon Titan Text Embeddings V2 at its default size. `BEDROCK_EMBEDDING_DIMENSIONS` must stay `1024` unless you add a migration that changes the column.

## Configure AWS Bedrock

1. In the Bedrock console, enable the embedding model and the chat model for your region.
2. Copy the example environment file:

```text
copy .env.example .env
```

On macOS or Linux:

```text
cp .env.example .env
```

3. Set `AWS_REGION` to the region where those models are enabled.
4. Either set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, or leave both empty and use the AWS credential chain already on the machine (an instance role, or credentials exported in the shell).
5. Set the model ids. The example values are:

```text
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
BEDROCK_CHAT_MODEL=us.anthropic.claude-sonnet-4-6
```

Use the model ids that are actually enabled in your account. A cross-region inference profile id is valid when that is how the model is published in your region.

6. Leave `BEDROCK_RERANK_MODEL` empty to use the local reranker. To rerank with Bedrock, set it to a rerank model you can invoke, for example `cohere.rerank-v3-5:0`. If that call fails, the API logs the failure and uses the local reranker for that request.

Do not commit `.env`. It is gitignored.

## Database

PostgreSQL with the `pgvector` extension stores documents, chunks, embeddings, a generated `tsvector`, conversations, and messages. The API applies `backend/alembic` migrations on startup inside Docker.

Compose creates a database named `search` with user `search` and password `search`, and points the API at `db:5432`. The `DATABASE_URL` in `.env` is for running the API on the host, where the database is on `localhost`. Compose overrides that URL for the `api` service.

Data lives in the `pgdata` volume. `docker compose down` keeps it. `docker compose down -v` deletes it.

## Run with Docker

From this directory, after `.env` exists:

```text
docker compose up --build
```

- Web UI: http://localhost:5173
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

The web container proxies `/api` to the API, so the browser talks to one origin.

## Run on the host

Use this when you want a local reload cycle. Start only the database from Compose, then run the API and the web app yourself. Commands below are for Windows PowerShell. On macOS or Linux, activate the virtualenv with `source .venv/bin/activate` and use `python3` if `python` is not Python 3.11+.

```text
docker compose up db -d
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:

```text
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to port 8000.

## Use the application

1. Add a `.pdf` or `.docx` file. Older `.doc` files are rejected. The file is parsed immediately.
2. PDF text is taken page by page, so citations can name a page. Word headings become section titles, and table cells are indexed. A scanned PDF with no text layer fails with a clear error. This version does not run OCR.
3. Start a chat, or just ask. The first question creates a chat. You can search every ready document or one document.
4. The answer is saved with the conversation. The Sources column lists the passages that were retrieved. A passage the model marked with `[n]` is labeled cited. Each source shows the file name and the page or section when the extractor had one.
5. Remove a document or a chat from the library. Removing a document deletes its chunks.

`POST /api/search` runs the same retrieval pipeline and returns the reranked passages without calling the chat model.

## Tests

From `backend`, with the virtualenv above:

```text
.venv\Scripts\python -m pytest
```

On macOS or Linux:

```text
pytest
```

The tests cover chunking, Word extraction, upload validation, BM25, reciprocal rank fusion, both rerankers, citation formatting, the retrieval pipeline, the no-match answer path, and the HTTP checks that do not need PostgreSQL or AWS. They do not call Bedrock and they do not start a database.

## Project layout

```text
semantic-document-search/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   ├── embeddings/
│   │   │   ├── retrieval/
│   │   │   ├── reranking/
│   │   │   └── generation/
│   │   ├── main.py
│   │   └── runtime.py
│   ├── alembic/
│   └── tests/
├── frontend/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Limits

- Embeddings and answers require Bedrock credentials and model access. Search and chat return an error the UI can show when Bedrock rejects the call. The failed document stays in the library with that error.
- Upload size defaults to 15 MB (`MAX_UPLOAD_BYTES`).
- Ingestion runs in the upload request. Very large files wait on that request instead of a background worker.
- The lexical pool is the top full-text matches (at least 50, or five times the candidate limit). BM25 rescores that pool. It is not a scan of every chunk for every query term outside the full-text match.
- Changing the embedding dimension requires a new migration. The running process refuses to start if `BEDROCK_EMBEDDING_DIMENSIONS` is not 1024.
