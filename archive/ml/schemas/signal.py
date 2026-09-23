from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, ConfigDict, Field
import numpy as np


class RawSignal(BaseModel):
    """Raw high-frequency 1-channel sensor acquisition block."""
    node_id: str = Field(..., description="Target sensor node code, e.g. NODE-001")
    sensor: str = Field(default="vibration", description="Sensor modality: 'vibration' or 'acoustic'")
    axis: str = Field(default="x", description="Sensor axis: 'x', 'y', 'z', or 'composite'")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of the first sample")
    sample_rate_hz: float = Field(default=1000.0, gt=0, description="Sampling rate in Hertz (e.g. 1000 Hz)")
    samples: Union[List[float], Any] = Field(..., description="Array or list of floating-point sensor raw samples")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_numpy(self) -> np.ndarray:
        if isinstance(self.samples, np.ndarray):
            return self.samples.astype(np.float64)
        return np.asarray(self.samples, dtype=np.float64)


class MultiAxisRawSignal(BaseModel):
    """Synchronized tri-axial vibration raw block (X, Y, Z)."""
    node_id: str = Field(..., description="Target sensor node code, e.g. NODE-001")
    sensor: str = Field(default="vibration", description="Sensor modality: 'vibration'")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of the first sample")
    sample_rate_hz: float = Field(default=1000.0, gt=0, description="Sampling rate in Hertz")
    x: Union[List[float], Any] = Field(..., description="Channel X raw samples")
    y: Union[List[float], Any] = Field(..., description="Channel Y raw samples")
    z: Union[List[float], Any] = Field(..., description="Channel Z raw samples")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SignalQualityResult(BaseModel):
    """Signal integrity audit result."""
    valid: bool = Field(..., description="True if signal passed all quality filters")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality index from 0.0 (corrupted) to 1.0 (pristine)")
    issues: List[str] = Field(default_factory=list, description="List of detected anomalies (e.g. FLATLINE, CLIPPING)")


class TimeDomainFeatures(BaseModel):
    """Statistical and mechanical time-domain indicators."""
    mean: float
    std: float
    var: float
    rms: float
    min: float
    max: float
    peak_to_peak: float
    peak: float
    crest_factor: float
    skewness: float
    kurtosis: float


class FrequencyDomainFeatures(BaseModel):
    """FFT-based spectral distribution indicators."""
    dominant_frequency_hz: float
    spectral_energy: float
    spectral_centroid_hz: float
    spectral_bandwidth_hz: float
    spectral_entropy: float
    band_energy: Dict[str, float] = Field(default_factory=dict)


class SingleAxisFeatures(BaseModel):
    """Combined time and frequency features for a single channel."""
    time_domain: TimeDomainFeatures
    frequency_domain: FrequencyDomainFeatures


class MultiAxisFeatures(BaseModel):
    """Complete 3-axis analysis with composite vector metrics."""
    x: SingleAxisFeatures
    y: SingleAxisFeatures
    z: SingleAxisFeatures
    aggregate: Dict[str, float]


class ProcessedSignalResult(BaseModel):
    """Standardized output of the signal processing pipeline."""
    processing_version: str = "0.1"
    feature_version: str = "0.1"
    timestamp: str
    sample_rate_hz: float
    window_samples: int
    quality: SignalQualityResult
    features: Union[SingleAxisFeatures, MultiAxisFeatures]
