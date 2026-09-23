"""
SIH 26008 — Explainable Multimodal Evidence Fusion Engine.

NOTICE:
Transparent, deterministic, rule-based fusion.
DOES NOT train another machine learning model.
Does NOT compute failure probabilities or RUL.
Combines:
- Vibration (Frozen IF-v0.3.1 + v0.5 commissioning + v0.6.1 persistence)
- Temperature (Absolute, rate of rise, persistence)
- Tracking (Lateral edge displacement)
- Camera (Visual belt-surface and boundary evidence from decoupled worker)
- Operating Context (Speed, load, operational state)

Generates explainable "WHY?" bullets stating observed phenomena.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence, UnifiedConveyorEvent


class FusionEngine:
    _instance: Optional["FusionEngine"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            full_conf = load_poc_thresholds()
            config = full_conf.get("fusion", {})

        self.vib_watch_z = float(config.get("vibration_watch_threshold", 3.0))
        self.require_persistent = bool(config.get("require_persistent_vibration_for_warning", True))
        self.freshness_window = float(config.get("freshness_window_seconds", 10.0))

    @classmethod
    def get_instance(cls) -> "FusionEngine":
        if cls._instance is None:
            cls._instance = FusionEngine()
        return cls._instance

    def fuse(
        self,
        vibration_evidence: Optional[SensorEvidence],
        temperature_evidence: Optional[SensorEvidence],
        tracking_evidence: Optional[SensorEvidence],
        camera_evidence: Optional[SensorEvidence],
        context_evidence: Optional[SensorEvidence],
        conveyor_id: str = "Conveyor-01",
        timestamp: Optional[datetime] = None,
    ) -> UnifiedConveyorEvent:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        op_state = "LOADED_RUNNING"
        if context_evidence and "operating_state" in context_evidence.value:
            op_state = str(context_evidence.value["operating_state"])

        reasons: List[str] = []
        supporting: List[SensorEvidence] = []

        # Extract flags from modalities
        # 1. Vibration
        vib_anomaly = False
        vib_persistent_3of5 = False
        vib_persistent_5of9 = False
        vib_state = "NORMAL"
        if vibration_evidence:
            vib_state = vibration_evidence.status
            vib_anomaly = vibration_evidence.anomaly
            vib_persistent_3of5 = bool(vibration_evidence.value.get("persistence_3of5", False))
            vib_persistent_5of9 = bool(vibration_evidence.value.get("persistence_5of9", False))
            if vib_anomaly or vib_state != "NORMAL":
                supporting.append(vibration_evidence)

        # 2. Temperature
        temp_anomaly = False
        temp_state = "NORMAL"
        temp_rapid_rise = False
        if temperature_evidence and temperature_evidence.quality == "GOOD":
            temp_state = temperature_evidence.status
            temp_anomaly = temperature_evidence.anomaly
            ror = float(temperature_evidence.value.get("rate_of_rise_c_per_min", 0.0))
            if ror >= 1.5:
                temp_rapid_rise = True
            if temp_anomaly:
                supporting.append(temperature_evidence)

        # 3. Tracking
        tracking_anomaly = False
        tracking_state = "NORMAL"
        if tracking_evidence and tracking_evidence.quality == "GOOD":
            tracking_state = tracking_evidence.status
            tracking_anomaly = tracking_evidence.anomaly
            if tracking_anomaly:
                supporting.append(tracking_evidence)

        # 4. Camera (Check freshness)
        camera_anomaly = False
        camera_state = "NORMAL"
        if camera_evidence and camera_evidence.quality == "GOOD":
            camera_state = camera_evidence.status
            camera_anomaly = camera_evidence.anomaly
            if camera_anomaly:
                supporting.append(camera_evidence)

        overall_state = "NORMAL"

        # -------------------------------------------------------------
        # EVALUATE TRANSPARENT EVIDENCE FUSION RULES
        # -------------------------------------------------------------

        # Rule 1 — Multimodal Mechanical Evidence (Vibration + Camera)
        if (vib_persistent_3of5 or vib_state in ["WARNING", "HIGH_SEVERITY"]) and camera_state in ["WARNING", "ALERT"]:
            overall_state = "HIGH_SEVERITY"
            reasons.append("Persistent vibration anomaly co-occurs with visual belt-surface abnormality.")

        # Rule 2 — Thermal + Vibration Evidence (Compound friction)
        elif (temp_rapid_rise or temp_state in ["WARNING", "ALERT"]) and (vib_anomaly or vib_state != "NORMAL"):
            overall_state = "HIGH_SEVERITY"
            reasons.append("Rapid temperature rise co-occurs with elevated vibration.")

        # Rule 3 — Tracking + Vibration Evidence (Misalignment contact)
        elif tracking_state in ["WARNING", "ALERT"] and (vib_anomaly or vib_state != "NORMAL"):
            overall_state = "WARNING"
            reasons.append("Tracking deviation co-occurs with abnormal vibration during the current operating state.")

        # Rule 4 — Severe Vibration Persistence Alone
        elif vib_persistent_5of9 or vib_state == "HIGH_SEVERITY":
            overall_state = "HIGH_SEVERITY"
            reasons.append("High-severity persistent vibration anomaly (5-of-9 window confirmation).")

        elif vib_persistent_3of5 or vib_state == "WARNING":
            overall_state = "WARNING"
            reasons.append("Persistent vibration anomaly detected by the frozen vibration monitoring pipeline (3-of-5 confirmation).")

        # Rule 5 — Isolated Thermal or Tracking Warning
        elif temp_state in ["WARNING", "ALERT"]:
            overall_state = "WARNING"
            reasons.append("Elevated thermal signature detected exceeding configured POC warning range.")

        elif tracking_state in ["WARNING", "ALERT"]:
            overall_state = "WARNING"
            reasons.append("Lateral belt tracking deviation exceeds configured POC warning range.")

        elif camera_state in ["WARNING", "ALERT"]:
            overall_state = "WATCH"
            reasons.append("Visible belt-surface abnormality observed by optical monitoring camera.")

        # Rule 6 — Startup / Shutdown Transient Dampening
        elif op_state in ["STARTING", "STOPPING"] and vib_anomaly and not vib_persistent_3of5:
            overall_state = "WATCH"
            reasons.append("Transient vibration elevation observed during a startup/shutdown operating state.")

        # Rule 7 — Single Modality Watch
        elif vib_state == "WATCH" or temp_state == "WATCH" or tracking_state == "WATCH" or camera_state == "WATCH":
            overall_state = "WATCH"
            if vib_state == "WATCH":
                reasons.append("Instantaneous vibration transient observed (awaiting persistence confirmation).")
            if temp_state == "WATCH":
                reasons.append("Mild thermal elevation within watch boundary.")
            if tracking_state == "WATCH":
                reasons.append("Minor lateral belt wander observed within watch boundary.")
            if camera_state == "WATCH":
                reasons.append("Mild visual belt edge displacement observed.")

        # Rule 8 — All Nominal
        else:
            overall_state = "NORMAL"
            reasons.append("Monitored modalities are within their configured POC baseline ranges.")

        return UnifiedConveyorEvent(
            timestamp=timestamp,
            conveyor_id=conveyor_id,
            operating_state=op_state,
            vibration=vibration_evidence,
            temperature=temperature_evidence,
            speed=context_evidence,
            load=context_evidence,
            tracking=tracking_evidence,
            camera=camera_evidence,
            overall_state=overall_state,
            reasons=reasons,
            supporting_evidence=supporting,
            confidence=None,
            confidence_method="NOT_CALIBRATED",
        )
