from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.core.database import get_db
from app.models.mine import Mine
from app.models.conveyor import Conveyor
from app.schemas.conveyor import ConveyorCreate, ConveyorResponse, ConveyorDetailResponse

router = APIRouter(prefix="/conveyors", tags=["Conveyors"])


@router.get("", response_model=List[ConveyorResponse])
def list_conveyors(mine_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve all conveyors, optionally filtered by mine_id."""
    query = select(Conveyor)
    if mine_id is not None:
        query = query.where(Conveyor.mine_id == mine_id)
    query = query.order_by(Conveyor.id.asc())
    conveyors = db.execute(query).scalars().all()
    return conveyors


@router.post("", response_model=ConveyorResponse, status_code=status.HTTP_201_CREATED)
def create_conveyor(payload: ConveyorCreate, db: Session = Depends(get_db)):
    """Register a new conveyor belt system."""
    # Verify parent mine exists
    mine = db.execute(select(Mine).where(Mine.id == payload.mine_id)).scalar_one_or_none()
    if not mine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mine with id {payload.mine_id} does not exist.",
        )

    conveyor = Conveyor(
        mine_id=payload.mine_id,
        name=payload.name,
        belt_type=payload.belt_type,
        length=payload.length,
        width=payload.width,
        status=payload.status,
    )
    db.add(conveyor)
    db.commit()
    db.refresh(conveyor)
    return conveyor


@router.get("/{conveyor_id}", response_model=ConveyorDetailResponse)
def get_conveyor(conveyor_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific conveyor belt including associated sensor nodes."""
    query = (
        select(Conveyor)
        .options(selectinload(Conveyor.sensor_nodes))
        .where(Conveyor.id == conveyor_id)
    )
    conveyor = db.execute(query).scalar_one_or_none()
    if not conveyor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conveyor with id {conveyor_id} not found.",
        )
    return conveyor
