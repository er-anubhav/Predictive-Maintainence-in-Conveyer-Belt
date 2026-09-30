from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.workers.camera_worker import CameraWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start decoupled optical camera background thread
    worker = CameraWorker.get_instance()
    worker.start()
    yield
    # Stop background thread and release video devices cleanly
    worker.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        description="FastAPI Backend for SIH 26008: Intelligent Conveyor Belt Health & Predictive Maintenance",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware configuration - allow local dev, tunnels, and Vercel domains
    application.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint at root and under api prefixes
    @application.get("/health", tags=["Health"])
    @application.get("/api/health", tags=["Health"])
    @application.get("/api/v1/health", tags=["Health"])
    def health_check():
        return {
            "status": "healthy",
            "service": "conveyor-maintenance-api",
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Mount API v1 router with configured prefix
    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = create_app()
