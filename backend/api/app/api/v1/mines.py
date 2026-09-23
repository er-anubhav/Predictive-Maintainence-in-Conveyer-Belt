from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.mine import Mine
from app.schemas.mine import MineCreate, MineResponse

router = APIRouter(prefix="/mines", tags=["Mines"])


@router.get("", response_model=List[MineResponse])
def list_mines(db: Session = Depends(get_db)):
    """Retrieve all registered mine sites."""
    mines = db.execute(select(Mine).order_by(Mine.id.asc())).scalars().all()
    return mines


@router.post("", response_model=MineResponse, status_code=status.HTTP_201_CREATED)
def create_mine(payload: MineCreate, db: Session = Depends(get_db)):
    """Register a new mine location."""
    mine = Mine(name=payload.name, location=payload.location)
    db.add(mine)
    db.commit()
    db.refresh(mine)
    return mine
