"""
SIH 26008 — Operating Context Engine.

NOTICE:
Operating context is contextual evidence, NOT a fault signal.
Distinguishes dynamic states:
- STOPPED
- STARTING (transient dynamic phase)
- IDLE (running unladen)
- EMPTY_RUNNING (running with minimal load)
- LOADED_RUNNING (standard production conveyance)
- STOPPING (deceleration transient)
- UNKNOWN

Uses externalized thresholds from config/poc_thresholds.yaml.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence


class OperatingContextEngine:
    _instance: Optional["OperatingContextEngine"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            full_conf = load_poc_thresholds()
            config = full_conf.get("operating_context", {})

        self.stopped_speed = float(config.get("stopped_speed_mps", 0.1))
        self.startup_threshold = float(config.get("startup_speed_threshold_mps", 2.0))
        self.nominal_speed = float(config.get("nominal_speed_mps", 2.80))
        self.idle_load = float(config.get("idle_load_percent", 15.0))
        self.loaded_load = float(config.get("loaded_load_percent", 40.0))
        self.overload = float(config.get("overload_percent", 90.0))
        self.trend_window = int(config.get("speed_trend_window_size", 5))
        self.pulley_diameter = float(config.get("pulley_diameter_meters", 0.50))
        self.encoder_ppr = int(config.get("pulley_encoder_pulses_per_rev", 60))

        # Node speed history: node_id -> list of float speeds
        self.speed_history: Dict[str, List[float]] = {}

    @classmethod
    def get_instance(cls) -> "OperatingContextEngine":
        if cls._instance is None:
            cls._instance = OperatingContextEngine()
        return cls._instance

    def calculate_speed_from_rpm(self, rpm: float) -> float:
        """Converts drive/tail pulley RPM into linear belt speed in m/s (v = pi * D * RPM / 60)."""
        import math
        return float((math.pi * self.pulley_diameter * rpm) / 60.0)

    def calculate_rpm_from_speed(self, speed_mps: float) -> float:
        """Converts linear belt speed into pulley RPM (RPM = v * 60 / (pi * D))."""
        import math
        if self.pulley_diameter <= 0.0:
            return 0.0
        return float((speed_mps * 60.0) / (math.pi * self.pulley_diameter))

    def evaluate(
        self,
        node_id: str,
        belt_speed_mps: float,
        load_percent: float,
        rpm: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        conveyor_id: str = "Conveyor-01",
    ) -> SensorEvidence:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # If RPM is directly provided by physical sensor, derive belt speed if speed is zero
        if rpm is not None and rpm > 0.0 and belt_speed_mps <= 0.0:
            belt_speed_mps = self.calculate_speed_from_rpm(rpm)
        elif rpm is None and belt_speed_mps > 0.0:
            rpm = self.calculate_rpm_from_speed(belt_speed_mps)
        elif rpm is None:
            rpm = 0.0

        if node_id not in self.speed_history:
            self.speed_history[node_id] = []
        hist = self.speed_history[node_id]
        hist.append(belt_speed_mps)
        if len(hist) > self.trend_window:
            hist.pop(0)

        # Determine speed trend
        trend = "STABLE"
        if len(hist) >= 3:
            diff = hist[-1] - hist[0]
            if diff > 0.3:
                trend = "INCREASING"
            elif diff < -0.3:
                trend = "DECREASING"

        # Classify state
        state = "UNKNOWN"
        reason = ""
        if belt_speed_mps < self.stopped_speed:
            state = "STOPPED"
            reason = f"Conveyor belt is stationary (speed {belt_speed_mps:.2f} m/s < {self.stopped_speed:.2f} m/s)."
        elif trend == "INCREASING" and belt_speed_mps < self.startup_threshold:
            state = "STARTING"
            reason = f"Belt speed is accelerating into operational range ({belt_speed_mps:.2f} m/s; trend {trend})."
        elif trend == "DECREASING" and belt_speed_mps < self.startup_threshold:
            state = "STOPPING"
            reason = f"Belt speed is decelerating toward stop ({belt_speed_mps:.2f} m/s; trend {trend})."
        elif belt_speed_mps >= self.startup_threshold:
            if load_percent < self.idle_load:
                state = "IDLE"
                reason = f"Belt running at speed ({belt_speed_mps:.2f} m/s) with negligible load ({load_percent:.1f}%)."
            elif load_percent < self.loaded_load:
                state = "EMPTY_RUNNING"
                reason = f"Belt running with light material transport ({load_percent:.1f}% load at {belt_speed_mps:.2f} m/s)."
            else:
                state = "LOADED_RUNNING"
                reason = f"Belt running under standard conveyance load ({load_percent:.1f}% load at {belt_speed_mps:.2f} m/s)."
        else:
            state = "STARTING" if trend == "INCREASING" else "IDLE"
            reason = f"Belt transitioning at {belt_speed_mps:.2f} m/s, load {load_percent:.1f}%."

        return SensorEvidence(
            timestamp=timestamp,
            conveyor_id=conveyor_id,
            sensor_id=node_id,
            modality="operating_context",
            status="NORMAL",
            anomaly=False,
            heuristic_severity=0.0,
            value={
                "operating_state": state,
                "belt_speed_mps": round(belt_speed_mps, 2),
                "load_percent": round(load_percent, 1),
                "speed_trend": trend,
            },
            quality="GOOD",
            reason=reason,
            method="DYNAMIC_STATE_MACHINE",
            confidence=None,
            confidence_method="NOT_CALIBRATED",
            is_simulated=False,
        )
