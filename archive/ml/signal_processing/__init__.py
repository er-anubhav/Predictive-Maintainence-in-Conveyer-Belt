"""
Core signal processing algorithms for SIH 26008 conveyor health monitoring.
"""

from ml.signal_processing.filtering import (
    remove_dc,
    detrend_signal,
    apply_butterworth_filter,
)
from ml.signal_processing.windowing import (
    WindowConfig,
    slice_windows,
)
from ml.signal_processing.time_features import (
    calculate_time_features,
)
from ml.signal_processing.frequency_features import (
    calculate_frequency_features,
    DEFAULT_FREQUENCY_BANDS,
)
from ml.signal_processing.quality import (
    SignalQualityAuditor,
    check_signal_quality,
)
from ml.signal_processing.pipeline import (
    VibrationPipeline,
)

__all__ = [
    "remove_dc",
    "detrend_signal",
    "apply_butterworth_filter",
    "WindowConfig",
    "slice_windows",
    "calculate_time_features",
    "calculate_frequency_features",
    "DEFAULT_FREQUENCY_BANDS",
    "SignalQualityAuditor",
    "check_signal_quality",
    "VibrationPipeline",
]
