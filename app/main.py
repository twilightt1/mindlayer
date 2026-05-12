import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from app.config import settings
from app.api.v1.router import api_router
from app.middleware.logging_middleware import LoggingMiddleware

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting RAG backend", environment=settings.ENVIRONMENT)
    try:
        from app.storage import ensure_bucket
        await ensure_bucket()
        log.info("MinIO bucket ready")
    except Exception as e:
        log.warning("MinIO init failed", error=str(e))
    yield
    log.info("Shutting down")


app = FastAPI(
    title="MindLayer API",
    version="1.0.0",
    description="Personal AI Second Brain — multi-source RAG, time-aware retrieval, knowledge graph, agentic actions.",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "1.0.0"})


@app.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    from app.services.health_service import check_readiness

    payload = await check_readiness()
    status_code = status.HTTP_200_OK if payload["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(payload, status_code=status_code)
