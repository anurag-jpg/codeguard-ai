"""
AI Bug Fixing Assistant — FastAPI Backend
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uvicorn

from backend.api.routes import router
from backend.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI Bug-Fixing Assistant starting …")
    yield
    logger.info("🛑 Shutting down gracefully …")


def create_app() -> FastAPI:

    app = FastAPI(
        title="AI Bug-Fixing Assistant",
        description="Automated code-repository analysis powered by RAG + LLM.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],
         allow_credentials=False,
          allow_methods=["*"],
         allow_headers=["*"],
)

    # Timing middleware
    @app.middleware("http")
    async def add_cors_and_timing(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )

    # API routes
    app.include_router(router, prefix="/api/v1")

    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "AI Bug Fixing Assistant API is running"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )