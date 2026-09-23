"""
Dataset Recording Utility for SIH 26008.

Saves raw sensor acquisition time series to compressed NumPy .npz files
with rich metadata for offline algorithm development and ML evaluation.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from ml import PROCESSING_VERSION

DATASETS_ROOT = Path(__file__).resolve().parent


def record_raw_dataset(
    node_id: str,
    conveyor_id: str,
    sensor: str,
    scenario: str,
    samples: Dict[str, np.ndarray] | np.ndarray,
    sample_rate_hz: float = 1000.0,
    timestamp: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Saves a raw recording to compressed .npz format with embedded metadata.
    """
    if timestamp is None:
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    if output_dir is None:
        subfolder = "vibration" if sensor == "vibration" else "acoustic"
        target_dir = DATASETS_ROOT / "raw" / subfolder
    else:
        target_dir = output_dir

    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{node_id}_{sensor}_{scenario}_{timestamp}.npz"
    file_path = target_dir / filename

    # Calculate duration
    if isinstance(samples, dict):
        first_arr = next(iter(samples.values()))
        duration_sec = len(first_arr) / sample_rate_hz
        arrays_to_save = samples
    else:
        duration_sec = len(samples) / sample_rate_hz
        arrays_to_save = {"samples": samples}

    metadata = {
        "node_id": node_id,
        "conveyor_id": conveyor_id,
        "sensor": sensor,
        "scenario": scenario,
        "timestamp": timestamp,
        "sample_rate_hz": sample_rate_hz,
        "duration_seconds": round(duration_sec, 3),
        "processing_version": PROCESSING_VERSION,
    }

    # Save arrays + metadata JSON string
    np.savez_compressed(
        file_path,
        metadata=json.dumps(metadata),
        **arrays_to_save,
    )

    return file_path


def load_raw_dataset(file_path: Path | str) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    """Loads a recorded .npz dataset and extracts metadata and array channels."""
    loaded = np.load(file_path)
    metadata = json.loads(str(loaded["metadata"]))
    arrays = {k: loaded[k] for k in loaded.files if k != "metadata"}
    return metadata, arrays
