"""
SIH 26008 — Deterministic Thermal Intelligence Engine.

NOTICE:
Uses externalized thresholds from config/poc_thresholds.yaml.
Evaluates:
1. Absolute temperature
2. Temperature rate-of-rise (°C/min)
3. Multi-window persistence
4. Sensor validity range

Uses evidence-based wording (what was observed), NOT unvalidated causal claims.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence


class ThermalIntelligence:
    _instance: Optional["ThermalIntelligence"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            full_conf = load_poc_thresholds()
            config = full_conf.get("temperature", {})

        self.normal_max = float(config.get("normal_max_c", 55.0))
        self.watch_max = float(config.get("watch_max_c", 65.0))
        self.warning_max = float(config.get("warning_max_c", 80.0))
        self.ror_watch = float(config.get("rate_of_rise_watch_c_per_min", 1.0))
        self.ror_warning = float(config.get("rate_of_rise_warning_c_per_min", 2.0))
        self.persistence_len = int(config.get("persistence_windows", 3))
        self.sensor_min = float(config.get("sensor_min_valid_c", -20.0))
        self.sensor_max = float(config.get("sensor_max_valid_c", 150.0))

        # Node history: node_id -> list of tuples (timestamp, temp_c, is_elevated)
        self.history: Dict[str, List[tuple]] = {}

    @classmethod
    def get_instance(cls) -> "ThermalIntelligence":
        if cls._instance is None:
            cls._instance = ThermalIntelligence()
        return cls._instance

    def evaluate(
        self,
        node_id: str,
        temperature_c: float,
        timestamp: Optional[datetime] = None,
        conveyor_id: str = "Conveyor-01",
    ) -> SensorEvidence:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # 1. Sensor Validity Check
        if temperature_c < self.sensor_min or temperature_c > self.sensor_max:
            return SensorEvidence(
                timestamp=timestamp,
                conveyor_id=conveyor_id,
                sensor_id=node_id,
                modality="temperature",
                status="ALERT",
                anomaly=True,
                heuristic_severity=1.0,
                value={
                    "temperature_c": round(temperature_c, 2),
                    "rate_of_rise_c_per_min": 0.0,
                    "valid_range": [self.sensor_min, self.sensor_max],
                },
                quality="INVALID",
                reason=f"Temperature reading {temperature_c:.1f}°C is outside valid sensor range ({self.sensor_min} to {self.sensor_max}°C).",
                method="SENSOR_RANGE_VALIDATION",
                confidence=None,
                confidence_method="NOT_CALIBRATED",
                is_simulated=False,
            )

        # 2. Track history & Calculate Rate-of-Rise (°C / min)
        if node_id not in self.history:
            self.history[node_id] = []

        hist = self.history[node_id]
        rate_of_rise = 0.0
        if hist:
            prev_ts, prev_temp, _ = hist[-1]
            dt_seconds = (timestamp - prev_ts).total_seconds()
            if dt_seconds >= 0.5:
                rate_of_rise = ((temperature_c - prev_temp) / dt_seconds) * 60.0

        # 3. Status determination based on absolute temp and rate of rise
        status = "NORMAL"
        anomaly = False
        heuristic_severity = 0.0
        reasons: List[str] = []

        # Check rate of rise
        rapid_rise = False
        if rate_of_rise >= self.ror_warning:
            rapid_rise = True
            reasons.append(
                f"Rate of temperature rise ({rate_of_rise:.1f}°C/min) exceeds configured POC warning threshold ({self.ror_warning:.1f}°C/min)"
            )
        elif rate_of_rise >= self.ror_watch:
            reasons.append(
                f"Rate of temperature rise ({rate_of_rise:.1f}°C/min) is elevated above watch threshold ({self.ror_watch:.1f}°C/min)"
            )

        # Check absolute temperature
        if temperature_c > self.warning_max:
            status = "ALERT"
            anomaly = True
            heuristic_severity = min(1.0, 0.8 + (temperature_c - self.warning_max) / 50.0)
            reasons.append(
                f"Bearing surface temperature ({temperature_c:.1f}°C) is above the configured POC critical alert threshold ({self.warning_max:.1f}°C)"
            )
        elif temperature_c > self.watch_max:
            status = "WARNING"
            anomaly = True
            heuristic_severity = 0.6 + 0.2 * ((temperature_c - self.watch_max) / (self.warning_max - self.watch_max))
            reasons.append(
                f"Bearing surface temperature ({temperature_c:.1f}°C) exceeds the configured POC warning threshold ({self.watch_max:.1f}°C)"
            )
        elif temperature_c > self.normal_max:
            status = "WATCH"
            anomaly = True
            heuristic_severity = 0.3 + 0.3 * ((temperature_c - self.normal_max) / (self.watch_max - self.normal_max))
            reasons.append(
                f"Bearing surface temperature ({temperature_c:.1f}°C) is elevated relative to the configured POC baseline ({self.normal_max:.1f}°C)"
            )
        elif rapid_rise:
            status = "WARNING"
            anomaly = True
            heuristic_severity = 0.65
        elif rate_of_rise >= self.ror_watch:
            status = "WATCH"
            anomaly = True
            heuristic_severity = 0.40

        if not reasons:
            reasons.append(
                f"Bearing temperature ({temperature_c:.1f}°C) is within nominal operating range (≤{self.normal_max:.1f}°C)"
            )

        # 4. Persistence tracking
        is_abnormal = status in ["WATCH", "WARNING", "ALERT"]
        hist.append((timestamp, temperature_c, is_abnormal))
        if len(hist) > 20:
            hist.pop(0)

        recent_abnormal_count = sum(1 for _, _, abn in hist[-self.persistence_len :])
        persistent = recent_abnormal_count >= self.persistence_len

        return SensorEvidence(
            timestamp=timestamp,
            conveyor_id=conveyor_id,
            sensor_id=node_id,
            modality="temperature",
            status=status,
            anomaly=anomaly,
            heuristic_severity=round(heuristic_severity, 3),
            value={
                "temperature_c": round(temperature_c, 2),
                "rate_of_rise_c_per_min": round(rate_of_rise, 2),
                "persistent": persistent,
                "window_count": len(hist),
            },
            quality="GOOD",
            reason="; ".join(reasons),
            method="DETERMINISTIC_THRESHOLD_AND_RATE_OF_RISE",
            confidence=None,
            confidence_method="NOT_CALIBRATED",
            is_simulated=False,
        )
