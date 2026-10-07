from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import Services
from app.api.routes import conversations, documents, health, search
from app.core.bedrock import bedrock_runtime_client
from app.core.config import get_settings
from app.core.errors import AppError
from app.services.embeddings.bedrock import BedrockEmbedder
from app.services.generation.bedrock import BedrockGenerator
from app.services.reranking.bedrock import build_reranker
from app.services.retrieval.lexical import LexicalSearch
from app.services.retrieval.vector import VectorSearch


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = bedrock_runtime_client(settings)
    app.state.services = Services(
        settings=settings,
        embedder=BedrockEmbedder(client, settings),
        generator=BedrockGenerator(client, settings),
        reranker=build_reranker(client, settings.bedrock_rerank_model),
        lexical=LexicalSearch(),
        vector=VectorSearch(),
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Semantic Document Search Engine",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, _app_error)
    app.include_router(health.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    return app


def _app_error(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app = create_app()
