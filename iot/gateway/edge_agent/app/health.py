import time
from typing import Dict, Any
import requests
from fastapi import APIRouter, Request
from app.config import settings
from app.models import GatewayHealth, GatewayMetrics
from app.metrics import metrics_manager

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=GatewayHealth)
def get_health(request: Request):
    """Returns edge gateway operational status, backend connectivity, and buffer size."""
    buffer = request.app.state.buffer
    forwarder = request.app.state.forwarder
    start_time = request.app.state.start_time

    # Test live backend connectivity
    backend_connected = False
    try:
        resp = requests.get(
            f"{settings.BACKEND_URL.rstrip('/')}/health",
            timeout=1.0,
        )
        if resp.status_code == 200:
            backend_connected = True
    except requests.RequestException:
        backend_connected = False

    queue_size = buffer.get_queue_size()
    uptime = round(time.time() - start_time, 1)

    return GatewayHealth(
        status="ok",
        backend_connected=backend_connected,
        queue_size=queue_size,
        last_forwarded_at=forwarder.last_forwarded_at,
        uptime_seconds=uptime,
    )


@router.get("/metrics", response_model=GatewayMetrics)
def get_metrics(request: Request):
    """Returns real-time gateway throughput and reliability telemetry."""
    buffer = request.app.state.buffer
    queue_size = buffer.get_queue_size()
    return metrics_manager.get_metrics(current_queue_size=queue_size)
