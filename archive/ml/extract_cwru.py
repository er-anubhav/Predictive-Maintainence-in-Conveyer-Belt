import json
from typing import Dict, Any, List
import numpy as np

from ml.schemas.common_feature import CommonBearingFeatureRecord
from ml.signal_processing.pipeline import VibrationPipeline


class CWRUFeatureExtractor:
    """
    Validates CWRU raw vibration waveforms against the SIH26008 zero-phase filtering
    and feature extraction pipeline before model training begins.
    """

    def __init__(self, sample_rate_hz: float = 12000.0, window_size: int = 2048, step_size: int = 1024):
        self.sample_rate_hz = sample_rate_hz
        self.window_size = window_size
        self.step_size = step_size
        self.pipeline = VibrationPipeline(
            sample_rate_hz=sample_rate_hz,
            filter_type="bandpass",
            cutoff_hz=(5.0, 4500.0), # suitable for 12 kHz CWRU vibration
            filter_order=4,
            detrend=True,
            remove_dc_bias=True,
        )

    def extract_from_signal(
        self,
        signal: np.ndarray,
        machine_id: str,
        label: str,
        fault_type: str = None,
        operating_condition: str = "1797_rpm_0hp",
    ) -> List[Dict[str, Any]]:
        """
        Segments continuous 1D raw vibration signal into overlapping windows,
        runs zero-phase SOS filtering, time-domain and FFT feature calculation.
        """
        records = []
        n_samples = len(signal)
        window_idx = 0

        for start in range(0, n_samples - self.window_size + 1, self.step_size):
            end = start + self.window_size
            window = signal[start:end]

            quality, single_axis = self.pipeline.process_single_axis(window, sample_rate_hz=self.sample_rate_hz)
            t_feat = single_axis.time_domain
            f_feat = single_axis.frequency_domain

            rec = CommonBearingFeatureRecord(
                dataset="cwru",
                sample_id=f"{machine_id}_w{window_idx:04d}",
                machine_id=machine_id,
                sensor="accelerometer",
                axis="DE_time",
                timestamp=None,
                sampling_rate_hz=self.sample_rate_hz,
                operating_condition=operating_condition,
                label=label,
                fault_type=fault_type,
                rms=round(float(t_feat.rms), 4),
                peak=round(float(t_feat.peak), 4),
                crest_factor=round(float(t_feat.crest_factor), 4),
                kurtosis=round(float(t_feat.kurtosis), 4),
                mean=round(float(t_feat.mean), 4),
                std=round(float(t_feat.std), 4),
                dominant_frequency_hz=round(float(f_feat.dominant_frequency_hz), 2),
                spectral_energy=round(float(f_feat.spectral_energy), 2),
                spectral_entropy=round(float(f_feat.spectral_entropy), 4) if f_feat.spectral_entropy else None,
            )
            records.append(rec.model_dump())
            window_idx += 1

        return records
