from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, DateTime, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sensor_node import SensorNode


class Telemetry(Base):
    __tablename__ = "telemetries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensor_node_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Vibration Metrics
    vibration_rms: Mapped[float] = mapped_column(Float, nullable=False)
    vibration_peak: Mapped[float] = mapped_column(Float, nullable=False)
    vibration_kurtosis: Mapped[float] = mapped_column(Float, nullable=False)
    crest_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dominant_frequency_hz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spectral_energy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Acoustic Emission Metrics
    acoustic_rms: Mapped[float] = mapped_column(Float, nullable=False)

    # Other Conveyor Dynamics Metrics
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    belt_speed: Mapped[float] = mapped_column(Float, nullable=False)
    load: Mapped[float] = mapped_column(Float, nullable=False)
    tracking_position: Mapped[float] = mapped_column(Float, nullable=False)

    # ML Inference & Evidence Fields (IF-v0.3.1 + v0.5 + v0.6.1)
    model_version: Mapped[Optional[str]] = mapped_column(nullable=True)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    composite_z_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    persistence_3of5: Mapped[Optional[bool]] = mapped_column(nullable=True)
    persistence_5of9: Mapped[Optional[bool]] = mapped_column(nullable=True)
    alert_state: Mapped[Optional[str]] = mapped_column(nullable=True)
    data_quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Multimodal Evidence & Fusion Fields
    operating_state: Mapped[Optional[str]] = mapped_column(nullable=True)
    multimodal_state: Mapped[Optional[str]] = mapped_column(nullable=True)
    fusion_reasons: Mapped[Optional[str]] = mapped_column(nullable=True)
    camera_status: Mapped[Optional[str]] = mapped_column(nullable=True)
    camera_frame_ref: Mapped[Optional[str]] = mapped_column(nullable=True)
    camera_is_simulated: Mapped[Optional[bool]] = mapped_column(nullable=True)

    sensor_node: Mapped["SensorNode"] = relationship(
        "SensorNode",
        back_populates="telemetries",
    )

    __table_args__ = (
        Index("ix_telemetry_sensor_timestamp", "sensor_node_id", "timestamp"),
        Index("ix_telemetry_sensor_sequence", "sensor_node_id", "sequence"),
    )
