from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conveyor import Conveyor
    from app.models.telemetry import Telemetry


class SensorNode(Base):
    __tablename__ = "sensor_nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conveyor_id: Mapped[int] = mapped_column(
        ForeignKey("conveyors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ONLINE")
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    conveyor: Mapped["Conveyor"] = relationship("Conveyor", back_populates="sensor_nodes")
    telemetries: Mapped[List["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="sensor_node",
        cascade="all, delete-orphan",
    )
