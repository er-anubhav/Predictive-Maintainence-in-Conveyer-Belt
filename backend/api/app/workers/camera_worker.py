"""
SIH 26008 — Decoupled Camera Worker & Evidence Store.

NOTICE:
Camera processing runs completely independent of the telemetry ingestion thread.
The worker updates the CameraEvidenceStore, which is polled by the fusion engine.
Freshness limit is enforced to avoid using stale visual evidence.
"""

import os
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import numpy as np
import cv2

from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence
from app.ml.camera_service import CameraService

logger = logging.getLogger("camera_worker")


class CameraEvidenceStore:
    """Thread-safe evidence store holding the latest camera analysis result."""
    _instance: Optional["CameraEvidenceStore"] = None

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_evidence: Optional[SensorEvidence] = None
        self._latest_frame_ref: Optional[str] = None
        self._latest_jpeg: Optional[bytes] = None
        self._last_updated: Optional[datetime] = None
        self._is_hardware: bool = False
        self._is_online: bool = True

    @classmethod
    def get_instance(cls) -> "CameraEvidenceStore":
        if cls._instance is None:
            cls._instance = CameraEvidenceStore()
        return cls._instance

    def update(
        self,
        evidence: SensorEvidence,
        frame_ref: str,
        jpeg_bytes: Optional[bytes] = None,
        is_hardware: bool = False,
        is_online: bool = True,
    ):
        with self._lock:
            self._latest_evidence = evidence
            self._latest_frame_ref = frame_ref
            if jpeg_bytes:
                self._latest_jpeg = jpeg_bytes
            self._last_updated = datetime.now(timezone.utc)
            self._is_hardware = is_hardware
            self._is_online = is_online

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def get_latest(self, max_age_seconds: float = 10.0) -> Optional[SensorEvidence]:
        with self._lock:
            if self._latest_evidence is None or self._last_updated is None:
                return None
            
            age = (datetime.now(timezone.utc) - self._last_updated).total_seconds()
            if age > max_age_seconds:
                stale_ev = self._latest_evidence.model_copy()
                stale_ev.quality = "DEGRADED"
                stale_ev.reason = f"Visual evidence is stale ({age:.1f}s > {max_age_seconds:.1f}s threshold)."
                return stale_ev

            return self._latest_evidence

    def get_latest_frame_ref(self) -> Optional[str]:
        with self._lock:
            return self._latest_frame_ref

    def get_health_status(self, max_age_seconds: float = 10.0) -> str:
        """Returns ONLINE | STALE | OFFLINE based on freshness and connection."""
        with self._lock:
            if not self._is_online or self._last_updated is None:
                return "OFFLINE"
            age = (datetime.now(timezone.utc) - self._last_updated).total_seconds()
            if age > max_age_seconds:
                return "STALE"
            return "ONLINE"


class CameraWorker:
    """
    Background worker that captures frames from camera sources or runs demo scenarios,
    analyzes them, writes annotated images, and publishes evidence.
    """
    _instance: Optional["CameraWorker"] = None

    def __init__(self, source: Optional[str] = None):
        conf = load_poc_thresholds().get("camera", {})
        default_dev = conf.get("source", conf.get("video_device", "0"))
        if default_dev == "demo" and os.path.exists("/dev/video0"):
            default_dev = "0"
        self.source = source or default_dev
        self.camera_service = CameraService.get_instance()
        self.evidence_store = CameraEvidenceStore.get_instance()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.active_scenario = "NORMAL"
        self._lock = threading.Lock()
        self.max_age_seconds = float(conf.get("max_evidence_age_seconds", 5.0))
        self._cap: Optional[cv2.VideoCapture] = None
        self.is_hardware_active = False
        self.flip_horizontal = True  # Mirror webcam by default
        self.flip_vertical = False

    @classmethod
    def get_instance(cls, source: Optional[str] = None) -> "CameraWorker":
        if cls._instance is None:
            cls._instance = CameraWorker(source=source)
        return cls._instance

    def set_flip(self, flip_horizontal: Optional[bool] = None, flip_vertical: Optional[bool] = None):
        with self._lock:
            if flip_horizontal is not None:
                self.flip_horizontal = flip_horizontal
            if flip_vertical is not None:
                self.flip_vertical = flip_vertical
            logger.info(f"CameraWorker flip updated: h={self.flip_horizontal}, v={self.flip_vertical}")

    def set_source(self, source: str):
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            self.source = source
            logger.info(f"CameraWorker source switched to: {source}")

    def set_demo_scenario(self, scenario: str):
        with self._lock:
            self.active_scenario = scenario
            logger.info(f"CameraWorker active scenario set to: {scenario}")
        # Immediately process one frame for the scenario
        self.step_once()

    def _get_capture_device(self) -> Optional[cv2.VideoCapture]:
        """Ensures a persistent open VideoCapture device with automatic reconnection."""
        if self.source == "demo":
            return None
        
        if self._cap is not None and self._cap.isOpened():
            return self._cap

        # Throttle open attempts so we do not spam V4L2 every loop
        now = time.time()
        if hasattr(self, "_last_open_attempt") and (now - self._last_open_attempt) < 3.0:
            return None
        self._last_open_attempt = now

        try:
            device_idx = int(self.source) if str(self.source).isdigit() else 0
            cap = cv2.VideoCapture(device_idx)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, test_f = cap.read()
                if ret and test_f is not None:
                    self._cap = cap
                    self.is_hardware_active = True
                    logger.info(f"Successfully opened hardware camera on device {device_idx}")
                    return self._cap
                cap.release()

            self._cap = None
            self.is_hardware_active = False
        except Exception as e:
            logger.warning(f"Failed to open camera device {self.source}: {e}")
            self._cap = None
            self.is_hardware_active = False

        return None

    def step_once(self, store_disk: bool = True) -> SensorEvidence:
        """Executes a single capture-analyze iteration. store_disk controls persistent JPEG writing."""
        with self._lock:
            scenario = self.active_scenario
            src = self.source

        is_hw = False
        is_online = True
        frame = None

        if src != "demo":
            cap = self._get_capture_device()
            if cap is not None and cap.isOpened():
                try:
                    ret, raw_frame = cap.read()
                    if ret and raw_frame is not None:
                        self._consecutive_read_failures = 0
                        # Flip video frame BEFORE analysis and HUD overlay so all metrics/text remain upright
                        if self.flip_horizontal and self.flip_vertical:
                            frame = cv2.flip(raw_frame, -1)
                        elif self.flip_horizontal:
                            frame = cv2.flip(raw_frame, 1)
                        elif self.flip_vertical:
                            frame = cv2.flip(raw_frame, 0)
                        else:
                            frame = raw_frame
                        is_hw = True
                    else:
                        self._consecutive_read_failures = getattr(self, "_consecutive_read_failures", 0) + 1
                        if self._consecutive_read_failures > 5:
                            logger.warning("Camera read failed repeatedly, releasing handle")
                            try:
                                cap.release()
                            except Exception:
                                pass
                            self._cap = None
                            self.is_hardware_active = False
                except Exception as e:
                    logger.error(f"Error reading from camera: {e}")
                    self._cap = None
                    self.is_hardware_active = False

        if frame is None:
            # Fall back to synthetic frame if hardware camera fails or is in demo mode
            raw_sim, _ = self.camera_service.generate_demo_frame(scenario)
            if self.flip_horizontal and self.flip_vertical:
                frame = cv2.flip(raw_sim, -1)
            elif self.flip_horizontal:
                frame = cv2.flip(raw_sim, 1)
            elif self.flip_vertical:
                frame = cv2.flip(raw_sim, 0)
            else:
                frame = raw_sim
            is_sim = True
            is_hw = False
            source_tag = "SIMULATED"
            if src != "demo":
                is_online = False
        else:
            is_sim = False
            is_hw = True
            source_tag = "USB_CAMERA"

        evidence, frame_ref, jpeg_bytes = self.camera_service.analyze_frame(
            frame, is_simulated=is_sim, store_disk=store_disk
        )
        evidence.source = source_tag
        evidence.is_simulated = is_sim
        self.evidence_store.update(
            evidence, frame_ref, jpeg_bytes=jpeg_bytes, is_hardware=is_hw, is_online=is_online
        )
        return evidence

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("CameraWorker background thread started.")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
        logger.info("CameraWorker stopped.")

    def _run_loop(self):
        last_disk_save = 0.0
        while self.running:
            try:
                now = time.time()
                # Persist to disk every 2.0s for compliance/evidence store; stream in-memory at high FPS
                store_disk = (now - last_disk_save) >= 2.0
                self.step_once(store_disk=store_disk)
                if store_disk:
                    last_disk_save = now
            except Exception as e:
                logger.error(f"Error in CameraWorker loop: {e}")
            time.sleep(0.04)  # ~20-25 FPS smooth video stream
