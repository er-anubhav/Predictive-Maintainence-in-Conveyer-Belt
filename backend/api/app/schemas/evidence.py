"""
SIH 26008 — Common Sensor Evidence Contract & Unified Conveyor Event Schema.

NOTICE:
heuristic_severity is a rule-derived indicator (0.0 - 1.0).
It is NOT a failure probability, rupture probability, or certified risk score.
Confidence is null with confidence_method: "NOT_CALIBRATED" unless mathematically calibrated.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class SensorEvidence(BaseModel):
    timestamp: datetime = Field(..., description="UTC timestamp of observation")
    conveyor_id: str = Field(..., description="Monitored conveyor identifier")
    sensor_id: str = Field(..., description="Sensor or node hardware identifier")
    modality: str = Field(
        ..., description="Modality type: vibration | temperature | tracking | camera | operating_context"
    )

    status: str = Field(..., description="Status classification: NORMAL | WATCH | WARNING | ALERT")
    anomaly: bool = Field(..., description="Boolean anomaly flag")

    heuristic_severity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rule-derived indicator (0.0 to 1.0). NOT a failure probability.",
    )

    value: Dict[str, Any] = Field(default_factory=dict, description="Raw and processed metric values")

    quality: str = Field(default="GOOD", description="Signal quality: GOOD | DEGRADED | INVALID")

    reason: str = Field(..., description="Evidence-based factual explanation (what was observed)")
    method: str = Field(..., description="Processing method or algorithm name")

    confidence: Optional[float] = Field(
        default=None, description="Calibrated confidence score if available; null otherwise"
    )
    confidence_method: Optional[str] = Field(
        default="NOT_CALIBRATED", description="Method used for confidence calibration"
    )

    is_simulated: bool = Field(default=False, description="True if generated/simulated, False if hardware")
    source: str = Field(default="REAL_HARDWARE", description="REAL_HARDWARE | SIMULATED | TEST_FIXTURE | USB_CAMERA")

    model_config = ConfigDict(from_attributes=True)


class HardwareHealthStatus(BaseModel):
    esp32: str = Field(default="ONLINE", description="ONLINE | OFFLINE")
    vibration: str = Field(default="GOOD", description="GOOD | DEGRADED | INVALID")
    temperature: str = Field(default="GOOD", description="GOOD | DEGRADED | INVALID")
    rpm: str = Field(default="GOOD", description="GOOD | DEGRADED | INVALID")
    tracking: str = Field(default="GOOD", description="GOOD | DEGRADED | INVALID")
    camera: str = Field(default="ONLINE", description="ONLINE | OFFLINE | STALE")


class UnifiedConveyorEvent(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of unified event evaluation")
    conveyor_id: str = Field(..., description="Conveyor identifier")
    operating_state: str = Field(
        ...,
        description="Operating context: STOPPED | STARTING | IDLE | EMPTY_RUNNING | LOADED_RUNNING | STOPPING | UNKNOWN",
    )
    system_mode: str = Field(default="REAL_HARDWARE", description="REAL_HARDWARE | DEMO_SIMULATED")
    hardware_health: Optional[HardwareHealthStatus] = None

    vibration: Optional[SensorEvidence] = None
    temperature: Optional[SensorEvidence] = None
    speed: Optional[SensorEvidence] = None
    load: Optional[SensorEvidence] = None
    tracking: Optional[SensorEvidence] = None
    camera: Optional[SensorEvidence] = None


    overall_state: str = Field(
        ..., description="Multimodal fusion state: NORMAL | WATCH | WARNING | HIGH_SEVERITY"
    )
    reasons: List[str] = Field(
        default_factory=list, description="List of evidence-based factual reasons explaining WHY"
    )
    supporting_evidence: List[SensorEvidence] = Field(
        default_factory=list, description="Collection of all supporting modality evidence items"
    )

    confidence: Optional[float] = Field(
        default=None, description="Not a failure probability; null unless formally calibrated"
    )
    confidence_method: Optional[str] = Field(default="NOT_CALIBRATED")

    model_config = ConfigDict(from_attributes=True)
