from typing import List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.sensor_node import SensorNode
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse


class TelemetryService:
    @staticmethod
    def resolve_sensor_node(db: Session, identifier: Union[str, int]) -> SensorNode:
        """Finds a sensor node by its node_code (e.g., 'NODE-001') or its integer primary key."""
        node = None
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            node = db.execute(select(SensorNode).where(SensorNode.id == int(identifier))).scalar_one_or_none()

        if not node and isinstance(identifier, str):
            node = db.execute(select(SensorNode).where(SensorNode.node_code == identifier)).scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor node '{identifier}' not found in registry.",
            )
        return node

    @classmethod
    def record_telemetry(cls, db: Session, payload: TelemetryCreate) -> TelemetryResponse:
        """Validates sensor node existence, checks for sequence duplication, updates node last_seen, and records telemetry."""
        node = cls.resolve_sensor_node(db, payload.sensor_node_id)

        # Idempotent deduplication check if sequence is present
        if payload.sequence is not None:
            existing_duplicate = db.execute(
                select(Telemetry).where(
                    Telemetry.sensor_node_id == node.id,
                    Telemetry.sequence == payload.sequence,
                )
            ).scalar_one_or_none()

            if existing_duplicate:
                # Return existing record idempotently without duplicate insertion
                return TelemetryResponse(
                    id=existing_duplicate.id,
                    sensor_node_id=existing_duplicate.sensor_node_id,
                    node_code=node.node_code,
                    sequence=existing_duplicate.sequence,
                    timestamp=existing_duplicate.timestamp,
                    vibration_rms=existing_duplicate.vibration_rms,
                    vibration_peak=existing_duplicate.vibration_peak,
                    vibration_kurtosis=existing_duplicate.vibration_kurtosis,
                    crest_factor=existing_duplicate.crest_factor,
                    dominant_frequency_hz=existing_duplicate.dominant_frequency_hz,
                    spectral_energy=existing_duplicate.spectral_energy,
                    acoustic_rms=existing_duplicate.acoustic_rms,
                    temperature=existing_duplicate.temperature,
                    belt_speed=existing_duplicate.belt_speed,
                    load=existing_duplicate.load,
                    tracking_position=existing_duplicate.tracking_position,
                )

        # Update last seen
        node.last_seen = payload.timestamp
        db.add(node)

        # ---------------------------------------------------------
        # REAL ML VIBRATION INFERENCE (IF-v0.3.1 + v0.5 + v0.6.1)
        # ---------------------------------------------------------
        from app.ml.vibration_inference import get_vibration_engine
        engine = get_vibration_engine()

        # If raw samples provided, extract features; otherwise use payload features
        if payload.raw_samples and len(payload.raw_samples) >= 4:
            ml_result = engine.process_vibration_window(
                samples=payload.raw_samples,
                sample_rate_hz=payload.sample_rate_hz or 1000.0,
                node_id=node.node_code,
            )
            v_rms = ml_result["features"]["rms"]
            v_peak = ml_result["features"]["peak"]
            v_crest = ml_result["features"]["crest_factor"]
            v_kurt = ml_result["features"]["kurtosis"]
            v_dom = ml_result["features"]["dominant_frequency_hz"]
            v_energy = ml_result["features"]["spectral_energy"]
        else:
            feat_dict = {
                "rms": float(payload.vibration_rms or 0.0),
                "peak": float(payload.vibration_peak or 0.0),
                "crest_factor": float(payload.crest_factor if payload.crest_factor is not None else ((payload.vibration_peak or 0.0) / (payload.vibration_rms or 1e-6))),
                "kurtosis": float(payload.vibration_kurtosis or 3.0),
                "dominant_frequency_hz": float(payload.dominant_frequency_hz or 20.0),
                "spectral_energy": float(payload.spectral_energy or ((payload.vibration_rms or 0.0)**2 * 100.0)),
            }
            ml_result = engine.process_features(feat_dict, node_id=node.node_code)
            v_rms = payload.vibration_rms
            v_peak = payload.vibration_peak
            v_crest = feat_dict["crest_factor"]
            v_kurt = payload.vibration_kurtosis
            v_dom = payload.dominant_frequency_hz
            v_energy = payload.spectral_energy

        # ---------------------------------------------------------
        # MULTIMODAL INTELLIGENCE & EVIDENCE GENERATION
        # ---------------------------------------------------------
        from app.schemas.evidence import SensorEvidence
        from app.ml.thermal_intelligence import ThermalIntelligence
        from app.ml.operating_context import OperatingContextEngine
        from app.ml.tracking_intelligence import TrackingIntelligence
        from app.ml.fusion_engine import FusionEngine
        from app.workers.camera_worker import CameraEvidenceStore

        conveyor_id_str = str(payload.conveyor_id or "Conveyor-01")

        # 1. Vibration SensorEvidence
        is_vib_anomaly = ml_result["alert_state"] != "NORMAL"
        vibration_evidence = SensorEvidence(
            timestamp=payload.timestamp,
            conveyor_id=conveyor_id_str,
            sensor_id=node.node_code,
            modality="vibration",
            status=ml_result["alert_state"],
            anomaly=is_vib_anomaly,
            heuristic_severity=round(min(1.0, ml_result["composite_z_deviation"] / 10.0), 3),
            value={
                "anomaly_score": ml_result["anomaly_score"],
                "composite_z_deviation": ml_result["composite_z_deviation"],
                "persistence_3of5": ml_result["persistent_3of5"],
                "persistence_5of9": ml_result["persistent_5of9"],
                "model_version": ml_result["model_version"],
            },
            quality="GOOD" if ml_result["data_quality"] >= 0.8 else "DEGRADED",
            reason=f"Isolation Forest IF-v0.3.1 composite deviation {ml_result['composite_z_deviation']:.2f}σ with dual persistence.",
            method="IF-v0.3.1+v0.5_COMMISSIONING+v0.6.1_PERSISTENCE",
            confidence=None,
            confidence_method="NOT_CALIBRATED",
            is_simulated=False,
        )

        is_sim = (
            payload.is_simulated is True
            or payload.source in ("SIMULATED", "DEMO_SIMULATED")
        )
        source_str = "DEMO_SIMULATED" if is_sim else (payload.source or "REAL_HARDWARE")

        vibration_evidence.source = source_str
        vibration_evidence.is_simulated = is_sim

        # 2. Operating Context
        context_engine = OperatingContextEngine.get_instance()
        context_evidence = context_engine.evaluate(
            node_id=node.node_code,
            belt_speed_mps=float(payload.belt_speed or 0.0),
            load_percent=float(payload.load or 0.0),
            rpm=float(payload.rpm) if payload.rpm is not None else None,
            timestamp=payload.timestamp,
            conveyor_id=conveyor_id_str,
        )
        context_evidence.source = source_str
        context_evidence.is_simulated = is_sim

        # 3. Thermal Intelligence
        thermal_engine = ThermalIntelligence.get_instance()
        thermal_evidence = thermal_engine.evaluate(
            node_id=node.node_code,
            temperature_c=float(payload.temperature or 0.0),
            timestamp=payload.timestamp,
            conveyor_id=conveyor_id_str,
        )
        thermal_evidence.source = source_str
        thermal_evidence.is_simulated = is_sim

        # 4. Tracking Intelligence (Simulated when no physical hardware attached)
        tracking_engine = TrackingIntelligence.get_instance()
        tracking_evidence = tracking_engine.evaluate(
            node_id=node.node_code,
            tracking_deviation_mm=float(payload.tracking_position or 0.0),
            timestamp=payload.timestamp,
            conveyor_id=conveyor_id_str,
        )
        tracking_evidence.source = "DEMO_SIMULATED" if is_sim else "SIMULATED"
        tracking_evidence.is_simulated = True

        # 5. Decoupled Camera Evidence Lookup (does NOT execute synchronous camera capture)
        camera_store = CameraEvidenceStore.get_instance()
        camera_evidence = camera_store.get_latest(max_age_seconds=10.0)
        camera_frame_ref = camera_store.get_latest_frame_ref()

        # 6. Explainable Evidence Fusion
        fusion_engine = FusionEngine.get_instance()
        unified_event = fusion_engine.fuse(
            vibration_evidence=vibration_evidence,
            temperature_evidence=thermal_evidence,
            tracking_evidence=tracking_evidence,
            camera_evidence=camera_evidence,
            context_evidence=context_evidence,
            conveyor_id=conveyor_id_str,
            timestamp=payload.timestamp,
        )

        # Hardware health diagnostics
        camera_health = camera_store.get_health_status()
        from app.schemas.evidence import HardwareHealthStatus
        hw_health = HardwareHealthStatus(
            esp32="ONLINE" if (not is_sim and payload.source == "REAL_HARDWARE") else "OFFLINE",
            vibration=vibration_evidence.quality,
            temperature=thermal_evidence.quality,
            rpm="GOOD" if payload.rpm is not None or payload.belt_speed is not None else "DEGRADED",
            tracking=tracking_evidence.quality,
            camera=camera_health,
        )
        unified_event.hardware_health = hw_health
        unified_event.system_mode = "DEMO_SIMULATED" if is_sim else "REAL_HARDWARE"

        telemetry = Telemetry(
            sensor_node_id=node.id,
            sequence=payload.sequence,
            timestamp=payload.timestamp,
            vibration_rms=v_rms,
            vibration_peak=v_peak,
            vibration_kurtosis=v_kurt,
            crest_factor=v_crest,
            dominant_frequency_hz=v_dom,
            spectral_energy=v_energy,
            acoustic_rms=payload.acoustic_rms,
            temperature=payload.temperature,
            belt_speed=payload.belt_speed,
            load=payload.load,
            tracking_position=payload.tracking_position,
            model_version=ml_result["model_version"],
            anomaly_score=ml_result["anomaly_score"],
            composite_z_deviation=ml_result["composite_z_deviation"],
            persistence_3of5=ml_result["persistent_3of5"],
            persistence_5of9=ml_result["persistent_5of9"],
            alert_state=ml_result["alert_state"],
            data_quality=ml_result["data_quality"],
            operating_state=unified_event.operating_state,
            multimodal_state=unified_event.overall_state,
            fusion_reasons="; ".join(unified_event.reasons),
            camera_status=camera_evidence.status if camera_evidence else "NORMAL",
            camera_frame_ref=camera_frame_ref,
            camera_is_simulated=camera_evidence.is_simulated if camera_evidence else True,
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        return TelemetryResponse(
            id=telemetry.id,
            sensor_node_id=telemetry.sensor_node_id,
            node_code=node.node_code,
            sequence=telemetry.sequence,
            timestamp=telemetry.timestamp,
            vibration_rms=telemetry.vibration_rms,
            vibration_peak=telemetry.vibration_peak,
            vibration_kurtosis=telemetry.vibration_kurtosis,
            crest_factor=telemetry.crest_factor,
            dominant_frequency_hz=telemetry.dominant_frequency_hz,
            spectral_energy=telemetry.spectral_energy,
            acoustic_rms=telemetry.acoustic_rms,
            temperature=telemetry.temperature,
            belt_speed=telemetry.belt_speed,
            load=telemetry.load,
            tracking_position=telemetry.tracking_position,
            model_version=telemetry.model_version,
            commissioning_version=ml_result["commissioning_version"],
            decision_layer_version=ml_result["decision_layer_version"],
            anomaly_score=telemetry.anomaly_score,
            composite_z_deviation=telemetry.composite_z_deviation,
            persistence_3of5=telemetry.persistence_3of5,
            persistence_5of9=telemetry.persistence_5of9,
            alert_state=telemetry.alert_state,
            data_quality=telemetry.data_quality,
            operating_state=telemetry.operating_state,
            multimodal_state=telemetry.multimodal_state,
            fusion_reasons=telemetry.fusion_reasons,
            camera_status=telemetry.camera_status,
            camera_frame_ref=telemetry.camera_frame_ref,
            camera_is_simulated=telemetry.camera_is_simulated,
            source=source_str,
            is_simulated=is_sim,
        )

    @classmethod
    def get_node_telemetry(
        cls,
        db: Session,
        sensor_node_identifier: Union[str, int],
        limit: int = 100,
    ) -> List[TelemetryResponse]:
        """Retrieves recent telemetry entries for a given sensor node, sorted newest first."""
        if str(sensor_node_identifier).upper() == "ALL":
            query = (
                select(Telemetry, SensorNode.node_code)
                .join(SensorNode, Telemetry.sensor_node_id == SensorNode.id)
                .order_by(desc(Telemetry.id))
                .limit(limit)
            )
            rows = db.execute(query).all()
            return [
                TelemetryResponse(
                    id=r.id,
                    sensor_node_id=r.sensor_node_id,
                    node_code=code,
                    sequence=r.sequence,
                    timestamp=r.timestamp,
                    vibration_rms=r.vibration_rms,
                    vibration_peak=r.vibration_peak,
                    vibration_kurtosis=r.vibration_kurtosis,
                    crest_factor=r.crest_factor,
                    dominant_frequency_hz=r.dominant_frequency_hz,
                    spectral_energy=r.spectral_energy,
                    acoustic_rms=r.acoustic_rms,
                    temperature=r.temperature,
                    belt_speed=r.belt_speed,
                    load=r.load,
                    tracking_position=r.tracking_position,
                    model_version=r.model_version or "IF-v0.3.1",
                    commissioning_version="v0.5",
                    decision_layer_version="v0.6.1",
                    anomaly_score=r.anomaly_score,
                    composite_z_deviation=r.composite_z_deviation,
                    persistence_3of5=r.persistence_3of5,
                    persistence_5of9=r.persistence_5of9,
                    alert_state=r.alert_state or "NORMAL",
                    data_quality=r.data_quality or 1.0,
                    operating_state=r.operating_state or "LOADED_RUNNING",
                    multimodal_state=r.multimodal_state or "NORMAL",
                    fusion_reasons=r.fusion_reasons,
                    camera_status=r.camera_status or "NORMAL",
                    camera_frame_ref=r.camera_frame_ref,
                    camera_is_simulated=r.camera_is_simulated or False,
                )
                for r, code in rows
            ]

        node = cls.resolve_sensor_node(db, sensor_node_identifier)

        query = (
            select(Telemetry)
            .where(Telemetry.sensor_node_id == node.id)
            .order_by(desc(Telemetry.id))
            .limit(limit)
        )
        records = db.execute(query).scalars().all()

        return [
            TelemetryResponse(
                id=r.id,
                sensor_node_id=r.sensor_node_id,
                node_code=node.node_code,
                sequence=r.sequence,
                timestamp=r.timestamp,
                vibration_rms=r.vibration_rms,
                vibration_peak=r.vibration_peak,
                vibration_kurtosis=r.vibration_kurtosis,
                crest_factor=r.crest_factor,
                dominant_frequency_hz=r.dominant_frequency_hz,
                spectral_energy=r.spectral_energy,
                acoustic_rms=r.acoustic_rms,
                temperature=r.temperature,
                belt_speed=r.belt_speed,
                load=r.load,
                tracking_position=r.tracking_position,
                model_version=r.model_version or "IF-v0.3.1",
                commissioning_version="v0.5",
                decision_layer_version="v0.6.1",
                anomaly_score=r.anomaly_score,
                composite_z_deviation=r.composite_z_deviation,
                persistence_3of5=r.persistence_3of5,
                persistence_5of9=r.persistence_5of9,
                alert_state=r.alert_state or "NORMAL",
                data_quality=r.data_quality or 1.0,
                operating_state=r.operating_state or "LOADED_RUNNING",
                multimodal_state=r.multimodal_state or "NORMAL",
                fusion_reasons=r.fusion_reasons,
                camera_status=r.camera_status or "NORMAL",
                camera_frame_ref=r.camera_frame_ref,
                camera_is_simulated=r.camera_is_simulated or False,
            )
            for r in records
        ]
