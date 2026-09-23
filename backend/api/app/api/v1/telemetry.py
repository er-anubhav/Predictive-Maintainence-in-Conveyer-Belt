from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def submit_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """
    Ingest a telemetry packet from a sensor node.
    Updates sensor node last_seen timestamp and persists vibration, acoustic, and conveyor metrics.
    """
    return TelemetryService.record_telemetry(db, payload)


@router.get("/{sensor_node_id}", response_model=List[TelemetryResponse])
def get_telemetry(
    sensor_node_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve chronological telemetry history for a specific sensor node.
    Accepts either the node hardware code (e.g. 'NODE-001') or database integer ID.
    """
    return TelemetryService.get_node_telemetry(db, sensor_node_id, limit=limit)
