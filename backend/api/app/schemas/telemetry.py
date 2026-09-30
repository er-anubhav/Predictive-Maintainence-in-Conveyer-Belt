from datetime import datetime
from typing import Union, Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


class VibrationBlock(BaseModel):
    rms: Optional[float] = Field(default=0.0, description="Vibration root-mean-square")
    peak: Optional[float] = Field(default=0.0, description="Peak vibration acceleration")
    kurtosis: Optional[float] = Field(default=3.0, description="Vibration kurtosis metric")
    crest_factor: Optional[float] = Field(default=None, description="Crest factor (peak / rms)")
    dominant_frequency_hz: Optional[float] = Field(default=None, description="Dominant spectral peak frequency in Hz")
    spectral_energy: Optional[float] = Field(default=None, description="Total spectral energy from FFT")


class AcousticBlock(BaseModel):
    rms: Optional[float] = Field(default=0.0, description="Acoustic emission signal RMS")


class TelemetryCreate(BaseModel):
    # Backward compatible: accepts sensor_node_id (e.g. "NODE-001" or 1) OR node_id
    sensor_node_id: Optional[Union[str, int]] = Field(
        default=None, description="Node hardware code (e.g. 'NODE-001') or database ID"
    )
    node_id: Optional[str] = Field(default=None, description="Canonical schema node identifier")
    conveyor_id: Optional[Union[str, int]] = Field(default=None, description="Conveyor identifier")
    schema_version: Optional[str] = Field(default="1.0", description="Contract schema version")
    sequence: Optional[int] = Field(default=None, description="Monotonic sequence number for deduplication")

    timestamp: datetime = Field(..., description="ISO 8601 UTC timestamp of sample reading")

    # Vibration Metrics (can be provided flat or in nested 'vibration' object)
    vibration_rms: Optional[float] = Field(default=None, description="Vibration root-mean-square in mm/s or g")
    vibration_peak: Optional[float] = Field(default=None, description="Peak vibration acceleration in g")
    vibration_kurtosis: Optional[float] = Field(default=None, description="Vibration kurtosis metric")
    crest_factor: Optional[float] = Field(default=None, description="Crest factor (peak / rms)")
    dominant_frequency_hz: Optional[float] = Field(default=None, description="Dominant spectral frequency in Hz")
    spectral_energy: Optional[float] = Field(default=None, description="Total spectral energy from FFT")
    vibration: Optional[VibrationBlock] = None

    # Acoustic Emission Metrics (can be provided flat or in nested 'acoustic' object)
    acoustic_rms: Optional[float] = Field(default=None, description="Acoustic emission signal RMS in Volts")
    acoustic: Optional[AcousticBlock] = None

    # Other Metrics
    temperature: Optional[float] = Field(default=0.0, description="Surface/bearing temperature in degrees Celsius")
    belt_speed: Optional[float] = Field(default=0.0, description="Linear conveyor belt speed in m/s")
    rpm: Optional[float] = Field(default=None, description="Drive pulley or roller rotational speed in RPM")
    pulse_count: Optional[int] = Field(default=None, description="Raw tachometer/encoder pulse counter")
    load: Optional[float] = Field(default=0.0, description="Belt load percentage (0-100%)")
    tracking_position: Optional[float] = Field(default=0.0, description="Lateral belt tracking deviation in mm")
    source: Optional[str] = Field(default=None, description="REAL_HARDWARE | DEMO_SIMULATED | SIMULATED | TEST_FIXTURE")
    is_simulated: Optional[bool] = Field(default=None, description="True if simulated, False if physical hardware")

    # Optional raw vibration samples for on-the-fly edge inference
    raw_samples: Optional[List[float]] = Field(default=None, description="Raw vibration samples if transmitting time series")
    sample_rate_hz: Optional[float] = Field(default=1000.0, description="Sampling rate in Hz for raw_samples")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # 1. Normalize node identifier
        if "sensor_node_id" not in data or data.get("sensor_node_id") is None:
            if "node_id" in data:
                data["sensor_node_id"] = data["node_id"]

        # 2. Extract nested vibration block if present
        vib = data.get("vibration")
        if isinstance(vib, dict):
            if "vibration_rms" not in data or data.get("vibration_rms") is None:
                data["vibration_rms"] = vib.get("rms", 0.0)
            if "vibration_peak" not in data or data.get("vibration_peak") is None:
                data["vibration_peak"] = vib.get("peak", 0.0)
            if "vibration_kurtosis" not in data or data.get("vibration_kurtosis") is None:
                data["vibration_kurtosis"] = vib.get("kurtosis", 3.0)
            if "crest_factor" not in data or data.get("crest_factor") is None:
                data["crest_factor"] = vib.get("crest_factor")
            if "dominant_frequency_hz" not in data or data.get("dominant_frequency_hz") is None:
                data["dominant_frequency_hz"] = vib.get("dominant_frequency_hz")
            if "spectral_energy" not in data or data.get("spectral_energy") is None:
                data["spectral_energy"] = vib.get("spectral_energy")
        elif "vibration_rms" not in data or data.get("vibration_rms") is None:
            data["vibration_rms"] = 0.0
            data["vibration_peak"] = 0.0
            data["vibration_kurtosis"] = 3.0

        # 3. Extract nested acoustic block if present
        ac = data.get("acoustic")
        if isinstance(ac, dict):
            if "acoustic_rms" not in data or data.get("acoustic_rms") is None:
                data["acoustic_rms"] = ac.get("rms", 0.0)
        elif "acoustic_rms" not in data or data.get("acoustic_rms") is None:
            data["acoustic_rms"] = 0.0

        # 4. Default other fields if missing
        if data.get("temperature") is None:
            data["temperature"] = 0.0
        if data.get("belt_speed") is None:
            data["belt_speed"] = 0.0
        if data.get("load") is None:
            data["load"] = 0.0
        if data.get("tracking_position") is None:
            data["tracking_position"] = 0.0

        return data


class TelemetryResponse(BaseModel):
    id: int
    sensor_node_id: int
    node_code: Optional[str] = None
    sequence: Optional[int] = None
    timestamp: datetime

    vibration_rms: float
    vibration_peak: float
    vibration_kurtosis: float
    crest_factor: Optional[float] = None
    dominant_frequency_hz: Optional[float] = None
    spectral_energy: Optional[float] = None

    acoustic_rms: float

    temperature: float
    belt_speed: float
    rpm: Optional[float] = None
    load: float
    tracking_position: float
    source: Optional[str] = "REAL_HARDWARE"
    is_simulated: Optional[bool] = False

    # ML Inference & Evidence Fields (IF-v0.3.1 + v0.5 + v0.6.1)
    model_version: Optional[str] = "IF-v0.3.1"
    commissioning_version: Optional[str] = "v0.5"
    decision_layer_version: Optional[str] = "v0.6.1"
    anomaly_score: Optional[float] = None
    composite_z_deviation: Optional[float] = None
    persistence_3of5: Optional[bool] = None
    persistence_5of9: Optional[bool] = None
    alert_state: Optional[str] = "NORMAL"
    data_quality: Optional[float] = 1.0

    # Multimodal Evidence & Fusion Fields
    operating_state: Optional[str] = "LOADED_RUNNING"
    multimodal_state: Optional[str] = "NORMAL"
    fusion_reasons: Optional[str] = None
    camera_status: Optional[str] = "NORMAL"
    camera_frame_ref: Optional[str] = None
    camera_is_simulated: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
