
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal, close_database
from app.middleware.error_handler import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.redis_client import connect_redis, close_redis


def configure_logging() -> None:
    """Configure structured JSON logging."""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            20 if not settings.DEBUG else 10
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_logging()

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""

    logger.info("Starting TripPlanner AI")

    try:
        await connect_redis()
        logger.info("Redis connected")

        yield

    finally:
        await close_redis()
        await close_database()
        logger.info("TripPlanner AI shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered multi-agent travel planning platform",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Request-ID",
        ],
    )

    application.add_middleware(RequestIDMiddleware)

    register_exception_handlers(application)

    @application.get(
        "/health/live",
        tags=["Health"],
    )
    async def liveness_check() -> dict[str, str]:
        """Check whether the application process is running."""
        return {
            "status": "alive",
            "application": settings.APP_NAME,
        }

    @application.get(
        "/health/ready",
        tags=["Health"],
    )
    async def readiness_check() -> dict[str, str]:
        """Check whether the database and Redis are reachable."""

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        redis = await connect_redis()
        await redis.ping()

        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected",
        }

    return application


app = create_application()
