from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.conveyor import Conveyor
from app.models.sensor_node import SensorNode
from app.schemas.sensor_node import SensorNodeCreate, SensorNodeResponse

router = APIRouter(prefix="/devices", tags=["Devices & Sensor Nodes"])


@router.get("", response_model=List[SensorNodeResponse])
def list_devices(conveyor_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve registered sensor nodes, optionally filtered by conveyor_id."""
    query = select(SensorNode)
    if conveyor_id is not None:
        query = query.where(SensorNode.conveyor_id == conveyor_id)
    query = query.order_by(SensorNode.id.asc())
    devices = db.execute(query).scalars().all()
    return devices


@router.post("", response_model=SensorNodeResponse, status_code=status.HTTP_201_CREATED)
def create_device(payload: SensorNodeCreate, db: Session = Depends(get_db)):
    """Register a new sensor node hardware unit."""
    # Verify conveyor exists
    conveyor = db.execute(select(Conveyor).where(Conveyor.id == payload.conveyor_id)).scalar_one_or_none()
    if not conveyor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conveyor with id {payload.conveyor_id} does not exist.",
        )

    # Check for duplicate node_code
    existing = db.execute(select(SensorNode).where(SensorNode.node_code == payload.node_code)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor node with code '{payload.node_code}' already exists.",
        )

    device = SensorNode(
        conveyor_id=payload.conveyor_id,
        node_code=payload.node_code,
        location=payload.location,
        firmware_version=payload.firmware_version,
        status=payload.status,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/{device_id}", response_model=SensorNodeResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a sensor node by ID or node_code."""
    node = None
    if device_id.isdigit():
        node = db.execute(select(SensorNode).where(SensorNode.id == int(device_id))).scalar_one_or_none()
    if not node:
        node = db.execute(select(SensorNode).where(SensorNode.node_code == device_id)).scalar_one_or_none()

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor node '{device_id}' not found.",
        )
    return node
