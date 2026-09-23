import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.buffer import SQLiteBuffer
from app.forwarder import ForwardingWorker
from app.receiver import router as receiver_router
from app.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite buffer if not already injected
    if not hasattr(app.state, "buffer") or app.state.buffer is None:
        app.state.buffer = SQLiteBuffer(settings.BUFFER_DB_PATH)
    if not hasattr(app.state, "forwarder") or app.state.forwarder is None:
        app.state.forwarder = ForwardingWorker(app.state.buffer)
    if not hasattr(app.state, "start_time") or app.state.start_time is None:
        app.state.start_time = time.time()

    # Start background forwarder thread unless disabled for unit testing
    auto_start = getattr(app.state, "auto_start_forwarder", True)
    if auto_start:
        app.state.forwarder.start()

    yield

    # Teardown: stop forwarder gracefully
    if hasattr(app.state, "forwarder") and app.state.forwarder:
        app.state.forwarder.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        description="Edge Gateway Agent for SIH 26008: Local Ingestion, Offline Buffering & Resilient Forwarding",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration for browser dashboard access
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routes
    application.include_router(receiver_router)
    application.include_router(health_router)

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=False,
    )
