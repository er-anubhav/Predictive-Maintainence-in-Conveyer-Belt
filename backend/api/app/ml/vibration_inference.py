"""
SIH 26008 — Unified Live Vibration Inference Engine.

Integrates:
- Frozen Base Anomaly Representation: IF-v0.3.1 (Isolation Forest, Standard 6 features)
- Machine-Agnostic Local Commissioning: v0.5 (20% run-in baseline for robust median/IQR)
- Temporal Persistence & Evidence Extraction: v0.6.1 (3-of-5 Warning, 5-of-9 High-Severity)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import numpy as np
import joblib

logger = logging.getLogger("vibration_inference")

FEATURE_COLUMNS = [
    "rms",
    "peak",
    "crest_factor",
    "kurtosis",
    "dominant_frequency_hz",
    "spectral_energy",
]


class VibrationInferenceEngine:
    _instance: Optional["VibrationInferenceEngine"] = None

    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            # Look in standard locations
            candidates = [
                "/home/anubhavtripathi/Documents/Projects/SIH26008/models/iforest/v0.3.1",
                os.path.join(os.path.dirname(__file__), "../../../models/iforest/v0.3.1"),
                os.path.abspath("models/iforest/v0.3.1"),
            ]
            for c in candidates:
                if os.path.exists(os.path.join(c, "model.joblib")):
                    model_dir = c
                    break
        
        if not model_dir or not os.path.exists(os.path.join(model_dir, "model.joblib")):
            raise FileNotFoundError(f"IF-v0.3.1 model artifact not found in candidate paths: {model_dir}")

        self.model_dir = os.path.abspath(model_dir)
        self.model_path = os.path.join(self.model_dir, "model.joblib")
        self.norm_path = os.path.join(self.model_dir, "normalization.json")
        self.thresh_path = os.path.join(self.model_dir, "threshold_config.json")

        # Load frozen base model
        self.model = joblib.load(self.model_path)
        with open(self.norm_path, "r") as f:
            self.normalization = json.load(f)
        with open(self.thresh_path, "r") as f:
            self.threshold_config = json.load(f)

        self.anomaly_threshold = float(self.threshold_config.get("anomaly_threshold", 0.59))
        self.calib_s_min = float(self.threshold_config.get("calibration", {}).get("s_min", 0.3532))
        self.calib_s_span = float(self.threshold_config.get("calibration", {}).get("s_span", 0.3408))

        # Node commissioning memory (Node ID -> commissioning state)
        self.node_commissioning: Dict[str, Dict[str, Any]] = {}
        # Node history ring buffer for temporal persistence (Node ID -> list of binary flags)
        self.node_history: Dict[str, List[int]] = {}

        logger.info(f"Loaded IF-v0.3.1 from {self.model_path}")

    @classmethod
    def get_instance(cls) -> "VibrationInferenceEngine":
        if cls._instance is None:
            cls._instance = VibrationInferenceEngine()
        return cls._instance

    @staticmethod
    def extract_features_from_samples(
        samples: Union[List[float], np.ndarray],
        sample_rate_hz: float = 1000.0,
    ) -> Dict[str, float]:
        """
        Extracts the exact Standard 6 features from raw 1D vibration time series.
        """
        arr = np.asarray(samples, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("Vibration samples array is empty")

        n = len(arr)
        rms = float(np.sqrt(np.mean(arr**2)))
        peak = float(np.max(np.abs(arr)))
        crest_factor = float(peak / (rms + 1e-12)) if rms > 1e-9 else 0.0

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        if std_val > 1e-9 and n > 3:
            from scipy import stats
            kurtosis = float(stats.kurtosis(arr, fisher=False, bias=False))
        else:
            kurtosis = 3.0

        # Frequency domain
        fft_vals = np.abs(np.fft.rfft(arr))
        freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)
        
        if len(fft_vals) > 1:
            dom_idx = int(np.argmax(fft_vals[1:]) + 1)
        else:
            dom_idx = int(np.argmax(fft_vals))
        dominant_frequency_hz = float(freqs[dom_idx])

        # Spectral energy = sum(|FFT|^2) / N
        spectral_energy = float(np.sum(fft_vals**2) / n)

        return {
            "rms": round(rms, 6),
            "peak": round(peak, 6),
            "crest_factor": round(crest_factor, 4),
            "kurtosis": round(kurtosis, 4),
            "dominant_frequency_hz": round(dominant_frequency_hz, 2),
            "spectral_energy": round(spectral_energy, 4),
        }

    def _normalize_features(self, feat_dict: Dict[str, float]) -> np.ndarray:
        """
        Applies frozen v0.3.1 training-set Z-score normalization.
        """
        x_norm = []
        for col in FEATURE_COLUMNS:
            val = float(feat_dict.get(col, 0.0))
            f_norm = self.normalization["features"][col]
            m = f_norm["mean"]
            s = f_norm["std"] if f_norm["std"] > 1e-9 else 1.0
            x_norm.append((val - m) / s)
        return np.array([x_norm], dtype=np.float64)

    def _update_commissioning(self, node_id: str, feat_dict: Dict[str, float]):
        """
        Tracks the first 20 readings as the local commissioning run-in baseline for node_id.
        """
        if node_id not in self.node_commissioning:
            self.node_commissioning[node_id] = {
                "count": 0,
                "buffer": {col: [] for col in FEATURE_COLUMNS},
                "median": None,
                "iqr": None,
                "commissioned": False,
            }

        comm = self.node_commissioning[node_id]
        if not comm["commissioned"]:
            comm["count"] += 1
            for col in FEATURE_COLUMNS:
                comm["buffer"][col].append(float(feat_dict.get(col, 0.0)))

            if comm["count"] >= 20:
                # Commissioning complete: compute robust median and IQR
                comm["median"] = {col: float(np.median(comm["buffer"][col])) for col in FEATURE_COLUMNS}
                comm["iqr"] = {
                    col: float(
                        max(1e-6, np.percentile(comm["buffer"][col], 75) - np.percentile(comm["buffer"][col], 25))
                    )
                    for col in FEATURE_COLUMNS
                }
                comm["commissioned"] = True
                comm["buffer"].clear()  # Free memory
        return comm

    def _compute_local_z_deviation(self, node_id: str, feat_dict: Dict[str, float]) -> tuple[float, Dict[str, float]]:
        """
        Computes robust per-feature deviations and composite Z relative to commissioned envelope.
        """
        comm = self.node_commissioning.get(node_id)
        deviations = {}
        if comm and comm["commissioned"]:
            z_vals = []
            for col in FEATURE_COLUMNS:
                med = comm["median"][col]
                iqr = comm["iqr"][col]
                denom = iqr / 1.349 if iqr > 1e-6 else 1.0
                z_dev = float(abs(feat_dict[col] - med) / denom)
                deviations[f"{col}_deviation"] = round(z_dev, 3)
                z_vals.append(z_dev)
            composite_z = round(float(np.max(z_vals)), 3)
        else:
            # Fallback to normalized z if not yet commissioned
            z_vals = []
            for col in FEATURE_COLUMNS:
                f_norm = self.normalization["features"][col]
                z_dev = float(abs(feat_dict[col] - f_norm["mean"]) / (f_norm["std"] + 1e-9))
                deviations[f"{col}_deviation"] = round(z_dev, 3)
                z_vals.append(z_dev)
            composite_z = round(float(np.max(z_vals)), 3)

        return composite_z, deviations

    def _update_persistence(self, node_id: str, is_anom: bool) -> tuple[bool, bool]:
        """
        Applies dual-rate temporal persistence (3-of-5 and 5-of-9 sliding window).
        """
        if node_id not in self.node_history:
            self.node_history[node_id] = []

        history = self.node_history[node_id]
        history.append(1 if is_anom else 0)
        if len(history) > 15:
            self.node_history[node_id] = history[-15:]

        # 3-of-5: at least 3 anomalies in last 5 windows
        sub_5 = self.node_history[node_id][-5:]
        p_3of5 = sum(sub_5) >= 3

        # 5-of-9: at least 5 anomalies in last 9 windows
        sub_9 = self.node_history[node_id][-9:]
        p_5of9 = sum(sub_9) >= 5

        return bool(p_3of5), bool(p_5of9)

    def process_features(
        self,
        features: Dict[str, float],
        node_id: str = "NODE-001",
        data_quality: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Inference entrypoint when precomputed Standard 6 features are provided.
        """
        # 1. Update local commissioning state
        self._update_commissioning(node_id, features)

        # 2. Base model inference (Frozen IF-v0.3.1)
        x_norm = self._normalize_features(features)
        
        # Scikit-learn score_samples: average anomaly score (higher means more normal)
        raw_score = float(-self.model.score_samples(x_norm)[0])
        # Rescale raw score to [0, 1] using v0.3.1 calibration span
        anomaly_score = round(float(np.clip((raw_score - self.calib_s_min) / (self.calib_s_span + 1e-9), 0.0, 1.0)), 4)

        # 3. Local Z-deviation
        composite_z, feature_deviations = self._compute_local_z_deviation(node_id, features)

        # 4. Instantaneous anomaly flag
        is_instantaneous_anomaly = (anomaly_score >= self.anomaly_threshold) or (composite_z >= 3.0)

        # 5. Temporal persistence
        p_3of5, p_5of9 = self._update_persistence(node_id, is_instantaneous_anomaly)

        # 6. Alert state classification
        if p_5of9:
            alert_state = "HIGH_SEVERITY"
        elif p_3of5:
            alert_state = "WARNING"
        elif is_instantaneous_anomaly:
            alert_state = "WATCH"
        else:
            alert_state = "NORMAL"

        return {
            "model_version": "IF-v0.3.1",
            "commissioning_version": "v0.5",
            "decision_layer_version": "v0.6.1",
            "anomaly_score": anomaly_score,
            "composite_z_deviation": composite_z,
            "persistent_3of5": p_3of5,
            "persistent_5of9": p_5of9,
            "features": {k: float(features.get(k, 0.0)) for k in FEATURE_COLUMNS},
            "feature_evidence": feature_deviations,
            "data_quality": data_quality,
            "confidence": None,
            "confidence_method": "NOT_CALIBRATED",
            "alert_state": alert_state,
        }

    def process_vibration_window(
        self,
        samples: Union[List[float], np.ndarray],
        sample_rate_hz: float = 1000.0,
        node_id: str = "NODE-001",
        data_quality: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Unified live inference entrypoint for raw vibration time series windows.
        """
        features = self.extract_features_from_samples(samples, sample_rate_hz=sample_rate_hz)
        return self.process_features(features, node_id=node_id, data_quality=data_quality)


# Global singleton access function
def get_vibration_engine() -> VibrationInferenceEngine:
    return VibrationInferenceEngine.get_instance()
