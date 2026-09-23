"""
SIH 26008 — Tracking & Alignment Intelligence Engine.

NOTICE:
Monitors lateral belt edge deviation in millimeters.
Uses externalized thresholds from config/poc_thresholds.yaml.
Uses evidence-based factual descriptions ("configured POC warning range"),
NOT unvalidated safety limits.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence


class TrackingIntelligence:
    _instance: Optional["TrackingIntelligence"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            full_conf = load_poc_thresholds()
            config = full_conf.get("tracking", {})

        self.normal_max = float(config.get("normal_max_abs_mm", 5.0))
        self.watch_max = float(config.get("watch_max_abs_mm", 12.0))
        self.warning_max = float(config.get("warning_max_abs_mm", 20.0))
        self.persistence_len = int(config.get("persistence_windows", 3))
        self.sensor_min = float(config.get("sensor_min_valid_mm", -50.0))
        self.sensor_max = float(config.get("sensor_max_valid_mm", 50.0))

        # Node history: node_id -> list of bool (is_abnormal)
        self.history: Dict[str, List[bool]] = {}

    @classmethod
    def get_instance(cls) -> "TrackingIntelligence":
        if cls._instance is None:
            cls._instance = TrackingIntelligence()
        return cls._instance

    def evaluate(
        self,
        node_id: str,
        tracking_deviation_mm: float,
        timestamp: Optional[datetime] = None,
        conveyor_id: str = "Conveyor-01",
    ) -> SensorEvidence:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # 1. Sensor Validity
        if tracking_deviation_mm < self.sensor_min or tracking_deviation_mm > self.sensor_max:
            return SensorEvidence(
                timestamp=timestamp,
                conveyor_id=conveyor_id,
                sensor_id=node_id,
                modality="tracking",
                status="ALERT",
                anomaly=True,
                heuristic_severity=1.0,
                value={
                    "tracking_deviation_mm": round(tracking_deviation_mm, 2),
                    "valid_range": [self.sensor_min, self.sensor_max],
                },
                quality="INVALID",
                reason=f"Lateral tracking reading ({tracking_deviation_mm:.1f} mm) is outside valid physical sensor limits ({self.sensor_min} to {self.sensor_max} mm).",
                method="SENSOR_RANGE_VALIDATION",
                confidence=None,
                confidence_method="NOT_CALIBRATED",
                is_simulated=False,
            )

        abs_dev = abs(tracking_deviation_mm)
        status = "NORMAL"
        anomaly = False
        heuristic_severity = 0.0
        reason = ""

        if abs_dev > self.warning_max:
            status = "ALERT"
            anomaly = True
            heuristic_severity = min(1.0, 0.8 + 0.2 * (abs_dev - self.warning_max) / 20.0)
            reason = f"Measured lateral belt deviation ({tracking_deviation_mm:+.1f} mm) exceeds the configured POC critical alert threshold (±{self.warning_max:.1f} mm)."
        elif abs_dev > self.watch_max:
            status = "WARNING"
            anomaly = True
            heuristic_severity = 0.6 + 0.2 * ((abs_dev - self.watch_max) / (self.warning_max - self.watch_max))
            reason = f"Measured lateral belt deviation ({tracking_deviation_mm:+.1f} mm) exceeds the configured POC warning range (±{self.watch_max:.1f} mm)."
        elif abs_dev > self.normal_max:
            status = "WATCH"
            anomaly = True
            heuristic_severity = 0.3 + 0.3 * ((abs_dev - self.normal_max) / (self.watch_max - self.normal_max))
            reason = f"Measured lateral belt deviation ({tracking_deviation_mm:+.1f} mm) is elevated relative to the configured POC baseline (±{self.normal_max:.1f} mm)."
        else:
            reason = f"Lateral tracking position ({tracking_deviation_mm:+.1f} mm) is centered within configured POC baseline tolerance (±{self.normal_max:.1f} mm)."

        # Persistence tracking
        if node_id not in self.history:
            self.history[node_id] = []
        hist = self.history[node_id]
        hist.append(anomaly)
        if len(hist) > 20:
            hist.pop(0)

        persistent = sum(1 for a in hist[-self.persistence_len :]) >= self.persistence_len

        return SensorEvidence(
            timestamp=timestamp,
            conveyor_id=conveyor_id,
            sensor_id=node_id,
            modality="tracking",
            status=status,
            anomaly=anomaly,
            heuristic_severity=round(heuristic_severity, 3),
            value={
                "tracking_deviation_mm": round(tracking_deviation_mm, 2),
                "absolute_deviation_mm": round(abs_dev, 2),
                "persistent": persistent,
                "history_windows": len(hist),
            },
            quality="GOOD",
            reason=reason,
            method="DETERMINISTIC_LATERAL_EDGE_THRESHOLD",
            confidence=None,
            confidence_method="NOT_CALIBRATED",
            is_simulated=False,
        )
