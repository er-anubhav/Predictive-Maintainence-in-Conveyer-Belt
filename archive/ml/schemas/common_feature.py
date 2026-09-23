from pydantic import BaseModel, Field
from typing import Optional


class CommonBearingFeatureRecord(BaseModel):
    """
    Unified cross-dataset schema for machine learning and edge inference.
    Where a dataset lacks a field, None (null in JSON) is strictly preserved.
    """
    # Provenance & Metadata
    dataset: str = Field(..., description="Dataset identifier: cwru, paderborn, nasa_ims, mimii, or conveyor_local")
    sample_id: str = Field(..., description="Unique window or frame identifier")
    machine_id: str = Field(..., description="Machine/Rig/Asset identifier, e.g., Conveyor-01, Motor-01, Rig-1")
    sensor: str = Field(..., description="Sensor hardware type: accelerometer, acoustic_sensor, microphone, tachometer")
    axis: str = Field(..., description="Axis or channel: DE_time, FE_time, x, y, z, mic_1")
    timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp string or relative timestamp; null if absent")
    sampling_rate_hz: float = Field(..., description="Sampling rate in Hertz (e.g. 12000, 20000, 64000, 1000)")
    operating_condition: Optional[str] = Field(None, description="Motor load, speed RPM, or operating state; null if unknown")
    label: str = Field(..., description="High-level ground truth: NORMAL, WATCH, ANOMALOUS")
    fault_type: Optional[str] = Field(None, description="Specific defect type: inner_race, ball, outer_race, cage, unbalance, baseline; null if normal")

    # Time-Domain Vibration & Signal Features
    rms: float = Field(..., description="Root Mean Square")
    peak: float = Field(..., description="Maximum absolute amplitude")
    crest_factor: float = Field(..., description="Peak / RMS ratio")
    kurtosis: float = Field(..., description="4th standardized statistical moment (impulsiveness indicator)")
    mean: float = Field(..., description="Signal arithmetic mean")
    std: float = Field(..., description="Standard deviation")

    # Frequency-Domain Spectral Features
    dominant_frequency_hz: Optional[float] = Field(None, description="Fundamental frequency peak f0; null if uncalculated")
    spectral_energy: Optional[float] = Field(None, description="Total sum of squared FFT amplitudes; null if uncalculated")
    spectral_entropy: Optional[float] = Field(None, description="Spectral entropy / Shannon entropy of power spectrum; null if uncalculated")
