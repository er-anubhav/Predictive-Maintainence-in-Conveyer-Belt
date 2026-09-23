from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, Tuple
import numpy as np

from ml import PROCESSING_VERSION, FEATURE_VERSION
from ml.schemas.signal import (
    SignalQualityResult,
    TimeDomainFeatures,
    FrequencyDomainFeatures,
    SingleAxisFeatures,
    MultiAxisFeatures,
    ProcessedSignalResult,
)
from ml.signal_processing.quality import check_signal_quality
from ml.signal_processing.filtering import remove_dc, detrend_signal, apply_butterworth_filter
from ml.signal_processing.time_features import calculate_time_features
from ml.signal_processing.frequency_features import calculate_frequency_features


class VibrationPipeline:
    """
    Standardized edge feature extraction pipeline for 1-axis and 3-axis vibration.
    Transforms raw time series into reliable engineering features.
    """

    def __init__(
        self,
        sample_rate_hz: float = 1000.0,
        filter_type: Optional[str] = "bandpass",
        cutoff_hz: Optional[Tuple[float, float]] = (2.0, 450.0),
        filter_order: int = 4,
        detrend: bool = True,
        remove_dc_bias: bool = True,
    ):
        self.sample_rate_hz = sample_rate_hz
        self.filter_type = filter_type
        self.cutoff_hz = cutoff_hz
        self.filter_order = filter_order
        self.detrend = detrend
        self.remove_dc_bias = remove_dc_bias

    def preprocess_channel(self, raw_samples: np.ndarray) -> np.ndarray:
        """Applies DC bias removal, detrending, and Butterworth filtering to a 1D channel."""
        arr = np.asarray(raw_samples, dtype=np.float64)

        if self.remove_dc_bias:
            arr = remove_dc(arr)

        if self.detrend:
            arr = detrend_signal(arr, trend_type="linear")

        if self.filter_type and self.cutoff_hz:
            arr = apply_butterworth_filter(
                arr,
                sample_rate_hz=self.sample_rate_hz,
                cutoff_hz=self.cutoff_hz,
                filter_type=self.filter_type,
                order=self.filter_order,
            )

        return arr

    def process_single_axis(
        self,
        samples: Union[list, np.ndarray],
        sample_rate_hz: Optional[float] = None,
    ) -> Tuple[SignalQualityResult, SingleAxisFeatures]:
        """Processes a single sensor channel."""
        fs = sample_rate_hz or self.sample_rate_hz
        raw_arr = np.asarray(samples, dtype=np.float64)

        # 1. Quality Check
        quality = check_signal_quality(raw_arr, sample_rate_hz=fs)
        if not quality.valid:
            # Return fallback empty/zeroed features if quality is invalid
            empty_time = TimeDomainFeatures(
                mean=0.0, std=0.0, var=0.0, rms=0.0, min=0.0, max=0.0,
                peak_to_peak=0.0, peak=0.0, crest_factor=0.0, skewness=0.0, kurtosis=0.0,
            )
            empty_freq = FrequencyDomainFeatures(
                dominant_frequency_hz=0.0, spectral_energy=0.0, spectral_centroid_hz=0.0,
                spectral_bandwidth_hz=0.0, spectral_entropy=0.0, band_energy={},
            )
            return quality, SingleAxisFeatures(time_domain=empty_time, frequency_domain=empty_freq)

        # 2. Preprocessing
        clean_samples = self.preprocess_channel(raw_arr)

        # 3. Time Domain Features
        time_feats = calculate_time_features(clean_samples)

        # 4. Frequency Domain Features (FFT)
        freq_feats = calculate_frequency_features(clean_samples, sample_rate_hz=fs)

        return quality, SingleAxisFeatures(time_domain=time_feats, frequency_domain=freq_feats)

    def process_multi_axis(
        self,
        x: Union[list, np.ndarray],
        y: Union[list, np.ndarray],
        z: Union[list, np.ndarray],
        sample_rate_hz: Optional[float] = None,
    ) -> Tuple[SignalQualityResult, MultiAxisFeatures]:
        """Processes 3 synchronized orthogonal vibration channels (X, Y, Z)."""
        fs = sample_rate_hz or self.sample_rate_hz

        q_x, feat_x = self.process_single_axis(x, sample_rate_hz=fs)
        q_y, feat_y = self.process_single_axis(y, sample_rate_hz=fs)
        q_z, feat_z = self.process_single_axis(z, sample_rate_hz=fs)

        # Combined Quality
        overall_valid = q_x.valid and q_y.valid and q_z.valid
        overall_score = min(q_x.quality_score, q_y.quality_score, q_z.quality_score)
        combined_issues = list(set(q_x.issues + q_y.issues + q_z.issues))
        combined_quality = SignalQualityResult(
            valid=overall_valid,
            quality_score=overall_score,
            issues=combined_issues,
        )

        # Multi-Axis Vector Aggregation
        rms_x = feat_x.time_domain.rms
        rms_y = feat_y.time_domain.rms
        rms_z = feat_z.time_domain.rms
        vector_rms = float(np.sqrt(rms_x**2 + rms_y**2 + rms_z**2))

        peak_x = feat_x.time_domain.peak
        peak_y = feat_y.time_domain.peak
        peak_z = feat_z.time_domain.peak
        vector_peak = float(max(peak_x, peak_y, peak_z))

        crest_factor = float(vector_peak / (vector_rms + 1e-12)) if vector_rms > 1e-9 else 0.0

        # Kurtosis: take maximum impulsive kurtosis observed across axes
        kurtosis = float(max(feat_x.time_domain.kurtosis, feat_y.time_domain.kurtosis, feat_z.time_domain.kurtosis))

        # Dominant frequency: identify which axis holds the highest spectral energy
        energies = {
            "x": feat_x.frequency_domain.spectral_energy,
            "y": feat_y.frequency_domain.spectral_energy,
            "z": feat_z.frequency_domain.spectral_energy,
        }
        dominant_axis = max(energies, key=energies.get)
        dominant_feats = {"x": feat_x, "y": feat_y, "z": feat_z}[dominant_axis]
        dominant_frequency_hz = dominant_feats.frequency_domain.dominant_frequency_hz

        total_spectral_energy = float(sum(energies.values()))

        aggregate = {
            "vector_rms": round(vector_rms, 4),
            "vector_peak": round(vector_peak, 4),
            "kurtosis": round(kurtosis, 4),
            "crest_factor": round(crest_factor, 4),
            "dominant_frequency_hz": round(dominant_frequency_hz, 2),
            "spectral_energy": round(total_spectral_energy, 4),
        }

        return combined_quality, MultiAxisFeatures(
            x=feat_x,
            y=feat_y,
            z=feat_z,
            aggregate=aggregate,
        )

    def process_window(
        self,
        samples: Union[np.ndarray, dict],
        sample_rate_hz: Optional[float] = None,
        timestamp: Optional[str] = None,
    ) -> ProcessedSignalResult:
        """
        Processes a single window either as 1D array or dict with 'x', 'y', 'z' channels.
        """
        fs = sample_rate_hz or self.sample_rate_hz
        ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if isinstance(samples, dict) and "x" in samples and "y" in samples and "z" in samples:
            window_size = len(samples["x"])
            quality, features = self.process_multi_axis(
                samples["x"], samples["y"], samples["z"], sample_rate_hz=fs
            )
        else:
            arr = np.asarray(samples, dtype=np.float64)
            window_size = len(arr)
            quality, features = self.process_single_axis(arr, sample_rate_hz=fs)

        return ProcessedSignalResult(
            processing_version=PROCESSING_VERSION,
            feature_version=FEATURE_VERSION,
            timestamp=ts,
            sample_rate_hz=fs,
            window_samples=window_size,
            quality=quality,
            features=features,
        )
