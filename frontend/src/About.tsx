const SITE = "https://folio-orcin-five.vercel.app";
const API = "https://api-production-6381.up.railway.app";
const REPO = "https://github.com/ShivanshSinghaL06/Folio";

export function About({ onNavigate }: { onNavigate: (href: string) => void }) {
  return (
    <article className="about">
      <p className="about-kicker">Folio</p>
      <h1>How this application works</h1>
      <p className="about-lead">
        Folio lets you upload PDF and Word files and ask questions in plain language. Each answer is grounded in
        retrieved passages and cites the file, and the page or section when the extractor had one. It was made by
        Shivansh Singhal.
      </p>

      <section>
        <h2>What it does</h2>
        <p>
          You add a <code>.pdf</code> or <code>.docx</code> file. Older <code>.doc</code> files are rejected, and a
          scanned PDF with no text layer fails with a clear error. This version does not run OCR. The file is parsed
          in the upload request, split into overlapping passages, and stored with a vector embedding and a full-text
          index.
        </p>
        <p>
          A question searches the ready documents, or one document you pick in the composer. Hybrid retrieval combines
          keyword matches and semantic matches, fuses the rankings, reranks the pool, and asks a chat model to answer
          only from those passages. The Sources cards under the reply show the file name, location, and excerpt. A
          passage the model marked with <code>[n]</code> is labeled Cited. A passage that was retrieved but not marked
          is labeled Retrieved.
        </p>
      </section>

      <section>
        <h2>Addresses</h2>
        <dl className="about-list">
          <div>
            <dt>Application</dt>
            <dd>
              <a href={SITE}>{SITE}</a>
            </dd>
          </div>
          <div>
            <dt>This page</dt>
            <dd>
              <a href={`${SITE}/about`}>{SITE}/about</a>
            </dd>
          </div>
          <div>
            <dt>API</dt>
            <dd>
              <a href={API}>{API}</a>
            </dd>
          </div>
          <div>
            <dt>Health</dt>
            <dd>
              <a href={`${API}/api/health`}>{API}/api/health</a>
            </dd>
          </div>
          <div>
            <dt>OpenAPI</dt>
            <dd>
              <a href={`${API}/docs`}>{API}/docs</a>
            </dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>
              <a href={REPO}>{REPO}</a>
            </dd>
          </div>
        </dl>
        <p>
          The browser talks only to the Vercel site. Requests to <code>/api</code> are proxied to the Railway API, so
          the page and the API share one public origin.
        </p>
      </section>

      <section>
        <h2>Tech stack</h2>
        <dl className="about-list">
          <div>
            <dt>Interface</dt>
            <dd>React 18 and TypeScript, built with Vite. The chat layout is a custom interface in the style of assistant-ui.</dd>
          </div>
          <div>
            <dt>API</dt>
            <dd>Python 3.12, FastAPI, and Uvicorn. Pydantic settings read the environment. Alembic applies schema migrations on startup.</dd>
          </div>
          <div>
            <dt>Database</dt>
            <dd>PostgreSQL 16 with pgvector. Chunks live in a 1024-dimension vector column. A generated tsvector supports full-text search.</dd>
          </div>
          <div>
            <dt>Models</dt>
            <dd>
              Amazon Bedrock in <code>ap-southeast-2</code>. Embeddings use Amazon Titan Text Embeddings V2. Answers use
              Claude Haiku 4.5. The app authenticates with a Bedrock API key.
            </dd>
          </div>
          <div>
            <dt>Hosting</dt>
            <dd>The website is a static Vite build on Vercel. The API and Postgres run as separate services on Railway.</dd>
          </div>
          <div>
            <dt>Local run</dt>
            <dd>Docker Compose starts Postgres, the API on port 8000, and the web app on port 5173. The same Python code runs on Windows and macOS.</dd>
          </div>
        </dl>
      </section>

      <section>
        <h2>Tools</h2>
        <ul>
          <li>pypdf reads PDF text page by page, so a citation can name a page.</li>
          <li>python-docx reads Word headings, body text, and table cells. Headings become section titles.</li>
          <li>boto3 calls Bedrock for embeddings and for the chat completion.</li>
          <li>SQLAlchemy and psycopg talk to Postgres. The pgvector Python package maps the embedding column.</li>
          <li>The lexical pool is selected with PostgreSQL full-text search and <code>ts_rank_cd</code>, then rescored with Okapi BM25 (<code>k1 = 1.5</code>, <code>b = 0.75</code>).</li>
          <li>Vector search is cosine distance on the 1024-dimension embedding.</li>
          <li>Reciprocal rank fusion merges the lexical and vector lists. A local reranker orders the fused candidates. A Bedrock rerank model is optional and unused in this deployment.</li>
          <li>pytest covers chunking, extraction, BM25, fusion, reranking, citations, and the HTTP checks that do not need Postgres or AWS.</li>
        </ul>
      </section>

      <section>
        <h2>Path of a document</h2>
        <ol>
          <li>The upload is checked for type and size. The default limit is 15 MB.</li>
          <li>Text is extracted with page numbers for PDFs, and with heading and table structure for Word files.</li>
          <li>The text is cut into overlapping chunks. The defaults are 1,200 characters with a 200-character overlap.</li>
          <li>Each chunk is embedded with Titan Text Embeddings V2 and stored beside its text and a full-text vector.</li>
          <li>The document stays in the library. A failed file keeps the error instead of disappearing.</li>
        </ol>
      </section>

      <section>
        <h2>Path of a question</h2>
        <ol>
          <li>The first question in an empty screen creates a conversation. Later questions stay on that chat.</li>
          <li>Full-text search builds a lexical candidate pool of at least 50 chunks, or five times the candidate limit. BM25 rescores that pool. It does not scan every chunk outside the full-text match.</li>
          <li>Vector search returns the nearest chunks by cosine distance.</li>
          <li>Reciprocal rank fusion combines the two rankings. The default candidate count is 20.</li>
          <li>The local reranker keeps the top 6 passages.</li>
          <li>Those passages, plus a short slice of chat history, go to Claude. The prompt asks for an answer that marks supporting passages with <code>[n]</code>.</li>
          <li>The answer and the citations are saved with the conversation.</li>
        </ol>
        <p>
          <code>POST /api/search</code> runs the same retrieval pipeline and returns the reranked passages without calling the chat model.
        </p>
      </section>

      <section>
        <h2>Code layout</h2>
        <p>
          Retrieval, reranking, embeddings, and generation are separate services behind small interfaces in{" "}
          <code>backend/app/services</code>. Ingestion lives in <code>services/ingestion</code>. HTTP routes for
          documents, conversations, search, and health live in <code>backend/app/api/routes</code>. The React app is
          in <code>frontend/src</code>.
        </p>
      </section>

      <p className="about-back">
        <a
          href="/"
          onClick={(event) => {
            event.preventDefault();
            onNavigate("/");
          }}
        >
          Back to chat
        </a>
      </p>
    </article>
  );
}
