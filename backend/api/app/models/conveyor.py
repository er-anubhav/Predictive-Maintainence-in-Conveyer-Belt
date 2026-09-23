from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.mine import Mine
    from app.models.sensor_node import SensorNode


class Conveyor(Base):
    __tablename__ = "conveyors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mine_id: Mapped[int] = mapped_column(
        ForeignKey("mines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    belt_type: Mapped[str] = mapped_column(String(100), nullable=False)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPERATIONAL")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    mine: Mapped["Mine"] = relationship("Mine", back_populates="conveyors")
    sensor_nodes: Mapped[List["SensorNode"]] = relationship(
        "SensorNode",
        back_populates="conveyor",
        cascade="all, delete-orphan",
    )
