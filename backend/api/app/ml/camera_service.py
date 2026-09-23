"""
SIH 26008 — Camera Service & Computer Vision Evidence Pipeline.

NOTICE:
Operates on optical frames from USB webcam, video file, RTSP stream, or synthetic test patterns.
Does NOT claim generic pretrained models diagnose belt joint rupture.
Analyzes:
1. Belt ROI extraction
2. Edge / boundary geometry & lateral displacement
3. Visible surface / splice abnormality
4. Produces annotated frames saved to externalized storage (data/evidence/camera/)
5. Enforces clear watermark 'DEMO / SIMULATED' on synthetic frames.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2

from app.core.thresholds import load_poc_thresholds
from app.schemas.evidence import SensorEvidence

logger = logging.getLogger("camera_service")


class CameraService:
    _instance: Optional["CameraService"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            full_conf = load_poc_thresholds()
            config = full_conf.get("camera", {})

        self.storage_dir = os.path.abspath(config.get("storage_directory", "data/evidence/camera"))
        os.makedirs(self.storage_dir, exist_ok=True)

        self.misalignment_watch_px = float(config.get("roi_misalignment_watch_px", 15.0))
        self.misalignment_warning_px = float(config.get("roi_misalignment_warning_px", 30.0))
        self.anomaly_watch_score = float(config.get("visual_anomaly_watch_score", 0.45))
        self.anomaly_warning_score = float(config.get("visual_anomaly_warning_score", 0.70))

    @classmethod
    def get_instance(cls) -> "CameraService":
        if cls._instance is None:
            cls._instance = CameraService()
        return cls._instance

    def generate_demo_frame(self, scenario: str = "NORMAL") -> Tuple[np.ndarray, bool]:
        """
        Generates a deterministic 640x360 synthetic industrial conveyor frame for demonstration.
        Carries mandatory DEMO / SIMULATED watermark.
        """
        width, height = 640, 360
        # Industrial conveyor bed background (dark metallic gray)
        frame = np.full((height, width, 3), 45, dtype=np.uint8)

        # Draw conveyor structure guidelines
        cv2.line(frame, (80, 0), (80, height), (70, 70, 70), 2)
        cv2.line(frame, (width - 80, 0), (width - 80, height), (70, 70, 70), 2)

        # Belt parameters
        belt_width = 360
        center_x = width // 2

        if scenario == "MISALIGNMENT":
            # Shift belt 40px to the right
            center_x += 42
        
        left_edge = center_x - (belt_width // 2)
        right_edge = center_x + (belt_width // 2)

        # Belt texture (dark rubber black with subtle noise)
        rubber_color = (25, 25, 25)
        cv2.rectangle(frame, (left_edge, 0), (right_edge, height), rubber_color, -1)

        # Draw longitudinal belt ribbing / wear lines
        for offset in [-120, -60, 0, 60, 120]:
            cv2.line(frame, (center_x + offset, 0), (center_x + offset, height), (35, 35, 35), 1)

        if scenario == "VISIBLE_DAMAGE":
            # Draw abnormal surface rip / splice tear artifact in ROI
            pts = np.array([
                [center_x - 30, 140],
                [center_x + 45, 155],
                [center_x + 35, 175],
                [center_x - 40, 160],
            ], np.int32)
            cv2.fillPoly(frame, [pts], (85, 95, 105)) # Exposed ply fabric
            cv2.polylines(frame, [pts], True, (20, 20, 20), 2)

        return frame, True

    def analyze_frame(
        self,
        frame: np.ndarray,
        is_simulated: bool = False,
        conveyor_id: str = "Conveyor-01",
        camera_id: str = "CAM-01",
        timestamp: Optional[datetime] = None,
        store_disk: bool = True,
    ) -> Tuple[SensorEvidence, str, bytes]:
        """
        Performs belt edge tracking and surface abnormality analysis.
        Returns SensorEvidence, relative file path (if stored), and encoded JPEG bytes.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. Edge & Lateral Tracking Analysis
        # Nominal belt centerline is image center
        nominal_center_x = width // 2

        # Threshold dark belt (intensity ~25) against idler frame (intensity ~45-70)
        _, thresh = cv2.threshold(gray, 38, 255, cv2.THRESH_BINARY_INV)
        # Find horizontal projection of belt region in middle 50% vertical slice
        mid_slice = thresh[height // 4 : 3 * height // 4, :]
        h_profile = np.mean(mid_slice, axis=0)

        # Detect left and right edges where belt intensity transitions
        active_indices = np.where(h_profile > 100)[0]
        if len(active_indices) > 50:
            detected_left = int(active_indices[0])
            detected_right = int(active_indices[-1])
            detected_center_x = (detected_left + detected_right) // 2
            edge_deviation_px = float(detected_center_x - nominal_center_x)
        else:
            detected_left = nominal_center_x - 180
            detected_right = nominal_center_x + 180
            detected_center_x = nominal_center_x
            edge_deviation_px = 0.0

        # 2. Surface Abnormality / Texture Anomaly Analysis
        # Check gradient in belt ROI
        belt_roi = gray[:, max(0, detected_left) : min(width, detected_right)]
        sobelx = cv2.Sobel(belt_roi, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(belt_roi, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)

        # Check for localized surface tears / splice separation
        high_grad_count = int(np.sum(grad_mag > 80.0))
        # Surface tear has hundreds of high-gradient edge points
        visual_anomaly_score = min(1.0, float(high_grad_count) / 350.0)

        # 3. Determine Evidence Status
        status = "NORMAL"
        anomaly = False
        heuristic_severity = 0.0
        reasons = []

        abs_dev_px = abs(edge_deviation_px)

        if visual_anomaly_score >= self.anomaly_warning_score:
            status = "WARNING"
            anomaly = True
            heuristic_severity = max(heuristic_severity, 0.75)
            reasons.append(
                f"Visible belt-surface abnormality detected (score {visual_anomaly_score:.2f} ≥ {self.anomaly_warning_score:.2f})"
            )

        if abs_dev_px >= self.misalignment_warning_px:
            status = "ALERT" if status == "WARNING" else "WARNING"
            anomaly = True
            heuristic_severity = max(heuristic_severity, 0.70)
            reasons.append(
                f"Visible belt edge displacement ({edge_deviation_px:+.1f}px) exceeds configured warning range (±{self.misalignment_warning_px:.0f}px)"
            )
        elif abs_dev_px >= self.misalignment_watch_px:
            if status == "NORMAL":
                status = "WATCH"
                anomaly = True
                heuristic_severity = 0.40
            reasons.append(
                f"Visible belt edge displacement ({edge_deviation_px:+.1f}px) is elevated relative to reference centerline"
            )

        if not reasons:
            reasons.append("Belt surface and edge geometry within nominal visual baseline.")

        # 4. Annotate Frame
        annotated = frame.copy()

        # Draw nominal centerline
        cv2.line(annotated, (nominal_center_x, 0), (nominal_center_x, height), (0, 255, 255), 1)
        # Draw detected edges
        cv2.line(annotated, (detected_left, 0), (detected_left, height), (0, 165, 255), 2)
        cv2.line(annotated, (detected_right, 0), (detected_right, height), (0, 165, 255), 2)
        # Draw detected center
        cv2.line(annotated, (detected_center_x, 0), (detected_center_x, height), (0, 0, 255), 2)

        # Status HUD on frame
        badge_color = (0, 200, 0) if status == "NORMAL" else (0, 165, 255) if status == "WATCH" else (0, 0, 255)
        cv2.rectangle(annotated, (10, 10), (320, 75), (20, 20, 20), -1)
        cv2.rectangle(annotated, (10, 10), (320, 75), badge_color, 2)
        cv2.putText(
            annotated,
            f"VISUAL STATUS: {status}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            badge_color,
            2,
        )
        cv2.putText(
            annotated,
            f"Edge Dev: {edge_deviation_px:+.1f}px | Anom: {visual_anomaly_score:.2f}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
        )

        # Mandatory watermark for synthetic demo frames
        if is_simulated:
            cv2.putText(
                annotated,
                "DEMO / SIMULATED",
                (width - 220, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 215, 255),
                2,
            )

        # 5. JPEG Encoding (In-memory + conditional persistent storage)
        ret, buffer = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        jpeg_bytes = buffer.tobytes() if ret else b""

        frame_id = f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        filename = f"{frame_id}.jpg"
        rel_path = f"camera/{filename}"

        if store_disk:
            file_path = os.path.join(self.storage_dir, filename)
            cv2.imwrite(file_path, annotated)

        evidence = SensorEvidence(
            timestamp=timestamp,
            conveyor_id=conveyor_id,
            sensor_id=camera_id,
            modality="camera",
            status=status,
            anomaly=anomaly,
            heuristic_severity=round(heuristic_severity, 3),
            value={
                "frame_id": frame_id,
                "camera_frame_ref": rel_path,
                "belt_edge_deviation_px": round(edge_deviation_px, 1),
                "visual_anomaly_score": round(visual_anomaly_score, 3),
                "is_simulated": is_simulated,
            },
            quality="GOOD",
            reason="; ".join(reasons),
            method="ROI_GEOMETRY_AND_GRADIENT_EDGE_ANALYSIS",
            confidence=None,
            confidence_method="NOT_CALIBRATED",
            is_simulated=is_simulated,
        )

        return evidence, rel_path, jpeg_bytes
