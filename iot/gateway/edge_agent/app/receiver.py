from fastapi import APIRouter, Depends, status, Request
from app.models import CanonicalTelemetry, IngestResponse
from app.metrics import metrics_manager

router = APIRouter(tags=["Ingestion"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_telemetry(payload: CanonicalTelemetry, request: Request):
    """
    Ingests an edge telemetry packet from an ESP32 or field sensor node.
    Enqueues the packet in the persistent SQLite buffer for resilient forwarding.
    """
    metrics_manager.inc_received()

    # Retrieve buffer and forwarder from application state
    buffer = request.app.state.buffer
    forwarder = request.app.state.forwarder

    is_success, is_duplicate, queue_id = buffer.enqueue(payload.model_dump())

    if is_duplicate:
        metrics_manager.inc_duplicate()
        return IngestResponse(
            status="duplicate",
            node_id=payload.node_id,
            sequence=payload.sequence,
            message=f"Packet sequence {payload.sequence} for {payload.node_id} already queued or processed.",
            queue_id=queue_id,
        )

    metrics_manager.inc_queued()
    forwarder.trigger_wake()

    return IngestResponse(
        status="queued",
        node_id=payload.node_id,
        sequence=payload.sequence,
        message="Packet buffered successfully for central uplink.",
        queue_id=queue_id,
    )
