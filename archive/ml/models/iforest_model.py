import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class IsolationForestAnomalyModel:
    """
    Milestone 4 Anomaly Detection Engine using Isolation Forest.
    Outputs:
      - anomaly_score: continuous score (normalized 0.0 to 1.0; 0=Normal, 1=Anomalous)
      - state: NORMAL, WATCH, ANOMALOUS (strictly no RUL or exact failure claims)
    """

    FEATURE_COLUMNS = [
        "rms",
        "peak",
        "crest_factor",
        "kurtosis",
        "dominant_frequency_hz",
        "spectral_energy",
    ]

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        watch_threshold: float = 0.55,
        anomaly_threshold: float = 0.70,
    ):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.watch_threshold = watch_threshold
        self.anomaly_threshold = anomaly_threshold

        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.is_fitted = False

    def _extract_feature_matrix(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """Extracts and imputes null values consistently."""
        matrix = []
        for r in records:
            row = []
            for col in self.FEATURE_COLUMNS:
                val = r.get(col)
                if val is None or np.isnan(val):
                    val = 0.0
                row.append(float(val))
            matrix.append(row)
        return np.array(matrix, dtype=np.float64)

    def fit(self, normal_train_records: List[Dict[str, Any]]):
        """Trains Isolation Forest strictly on baseline operational data."""
        X = self._extract_feature_matrix(normal_train_records)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True

    def predict_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Inference for a single record."""
        return self.predict_records([record])[0]

    def predict_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Inference for a batch of records."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")

        X = self._extract_feature_matrix(records)
        X_scaled = self.scaler.transform(X)

        # Raw score: lower values represent anomalies, higher represent normal
        raw_scores = self.model.decision_function(X_scaled)

        # Normalize score into [0.0, 1.0] where 1.0 is most anomalous
        # decision_function typically lies in [-0.5, 0.5]
        anomaly_scores = 1.0 / (1.0 + np.exp(raw_scores * 6.0))

        results = []
        for i, score in enumerate(anomaly_scores):
            s = float(score)
            if s >= self.anomaly_threshold:
                state = "ANOMALOUS"
            elif s >= self.watch_threshold:
                state = "WATCH"
            else:
                state = "NORMAL"

            results.append({
                "anomaly_score": round(s, 4),
                "state": state,
                "raw_decision_score": round(float(raw_scores[i]), 4),
            })
        return results

    def export(self, export_dir: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Exports production-ready artifacts for standalone edge execution without Colab:
        - model.joblib
        - normalization.json
        - feature_config.json
        - metadata.json
        """
        os.makedirs(export_dir, exist_ok=True)

        # 1. Serialized scikit-learn model
        model_path = os.path.join(export_dir, "model.joblib")
        joblib.dump(self.model, model_path)

        # 2. Normalization scaler parameters
        norm_data = {
            "scaler_type": "StandardScaler",
            "features": self.FEATURE_COLUMNS,
            "mean": self.scaler.mean_.tolist(),
            "scale": self.scaler.scale_.tolist(),
            "var": self.scaler.var_.tolist(),
        }
        with open(os.path.join(export_dir, "normalization.json"), "w") as f:
            json.dump(norm_data, f, indent=2)

        # 3. Feature configuration
        feature_config = {
            "feature_version": "v1.0.0",
            "feature_columns": self.FEATURE_COLUMNS,
            "required_fields": ["rms", "peak", "crest_factor", "kurtosis"],
            "optional_fields": ["dominant_frequency_hz", "spectral_energy"],
            "imputation": "zero",
        }
        with open(os.path.join(export_dir, "feature_config.json"), "w") as f:
            json.dump(feature_config, f, indent=2)

        # 4. Model metadata
        meta = {
            "model_type": "IsolationForest",
            "version": "v0.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "contamination": self.contamination,
                "random_state": self.random_state,
                "watch_threshold": self.watch_threshold,
                "anomaly_threshold": self.anomaly_threshold,
            },
            "states": ["NORMAL", "WATCH", "ANOMALOUS"],
            "disclaimer": "Scores represent statistical distance/anomaly score, NOT failure probability or RUL.",
        }
        if metadata:
            meta.update(metadata)

        with open(os.path.join(export_dir, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)

        print(f"Exported artifact bundle successfully to: {export_dir}")
