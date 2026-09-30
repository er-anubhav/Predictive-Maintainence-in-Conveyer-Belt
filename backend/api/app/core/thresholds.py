"""
SIH 26008 — Configuration Loader for POC Demonstration Thresholds.

NOTICE:
POC DEMONSTRATION THRESHOLDS ONLY
FIELD CALIBRATION REQUIRED
NOT SAFETY LIMITS
"""

import os
from typing import Dict, Any
import yaml

DEFAULT_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../config/poc_thresholds.yaml")
)

_CACHED_CONFIG: Dict[str, Any] = {}


def load_poc_thresholds(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    global _CACHED_CONFIG
    if _CACHED_CONFIG:
        return _CACHED_CONFIG

    if not os.path.exists(config_path):
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[4]
        candidates = [
            str(repo_root / "config" / "poc_thresholds.yaml"),
            os.path.abspath("config/poc_thresholds.yaml"),
            os.path.abspath("../../config/poc_thresholds.yaml"),
            os.path.abspath("../config/poc_thresholds.yaml"),
        ]
        for c in candidates:
            if os.path.exists(c):
                config_path = c
                break


    with open(config_path, "r") as f:
        _CACHED_CONFIG = yaml.safe_load(f)

    return _CACHED_CONFIG
