from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class VibrationData(BaseModel):
    rms: Optional[float] = Field(default=0.0, description="Vibration RMS (g or mm/s)")
    peak: Optional[float] = Field(default=0.0, description="Peak acceleration (g)")
    kurtosis: Optional[float] = Field(default=3.0, description="Vibration kurtosis metric")
    crest_factor: Optional[float] = Field(default=None, description="Crest factor")
    dominant_frequency_hz: Optional[float] = Field(default=None, description="Dominant frequency in Hz")
    spectral_energy: Optional[float] = Field(default=None, description="Spectral energy")

    model_config = ConfigDict(extra="allow")


class AcousticData(BaseModel):
    rms: Optional[float] = Field(default=0.0, description="Acoustic emission RMS (V)")


class CanonicalTelemetry(BaseModel):
    schema_version: str = Field(default="1.0", description="Canonical schema version")
    node_id: str = Field(..., description="Unique edge sensor hardware identifier")
    conveyor_id: str = Field(..., description="Associated conveyor asset identifier")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    sequence: int = Field(..., ge=0, description="Monotonically increasing sequence number")

    # Modular sensor payload
    vibration: Optional[VibrationData] = None
    acoustic: Optional[AcousticData] = None
    temperature: Optional[float] = Field(default=None, description="Bearing/belt temperature in °C")
    belt_speed: Optional[float] = Field(default=None, description="Linear belt velocity in m/s")
    rpm: Optional[float] = Field(default=None, description="Rotational speed in RPM")
    pulse_count: Optional[int] = Field(default=None, description="Pulley pulse count")
    load: Optional[float] = Field(default=None, description="Belt loading percentage")
    tracking_position: Optional[float] = Field(default=None, description="Lateral tracking deviation in mm")
    source: Optional[str] = Field(default="REAL_HARDWARE", description="REAL_HARDWARE | SIMULATED | TEST_FIXTURE")

    model_config = ConfigDict(extra="allow")


class IngestResponse(BaseModel):
    status: str = Field(..., description="'queued' or 'duplicate'")
    node_id: str
    sequence: int
    message: str
    queue_id: Optional[int] = None


class GatewayHealth(BaseModel):
    status: str = "ok"
    backend_connected: bool
    queue_size: int
    last_forwarded_at: Optional[str] = None
    uptime_seconds: float


class GatewayMetrics(BaseModel):
    packets_received: int
    packets_queued: int
    packets_forwarded: int
    packets_failed: int
    duplicate_packets: int
    current_queue_size: int
