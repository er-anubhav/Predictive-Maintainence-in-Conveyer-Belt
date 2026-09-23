from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Generator
import numpy as np


class WindowConfig:
    """Configuration for temporal windowing of continuous or buffered time series."""

    def __init__(
        self,
        window_size: int = 1024,
        overlap: float = 0.50,
        window_function: str = "rect",
    ):
        if window_size <= 0:
            raise ValueError(f"window_size must be positive, got {window_size}")
        if not (0.0 <= overlap < 1.0):
            raise ValueError(f"overlap must be in range [0.0, 1.0), got {overlap}")

        self.window_size = window_size
        self.overlap = overlap
        self.step_size = max(1, int(window_size * (1.0 - overlap)))
        self.window_function = window_function.lower()

    def get_taper_window(self) -> np.ndarray:
        """Returns the taper window weights (e.g. Hann, Hamming, Rectangular)."""
        if self.window_function == "hann":
            return np.hanning(self.window_size)
        elif self.window_function == "hamming":
            return np.hamming(self.window_size)
        elif self.window_function in ("rect", "rectangular", "boxcar"):
            return np.ones(self.window_size, dtype=np.float64)
        else:
            raise ValueError(f"Unsupported window function: {self.window_function}")


def slice_windows(
    samples: np.ndarray,
    sample_rate_hz: float = 1000.0,
    start_timestamp: Optional[datetime] = None,
    config: Optional[WindowConfig] = None,
    apply_taper: bool = False,
) -> Generator[Tuple[np.ndarray, Optional[datetime], int], None, None]:
    """
    Slices a 1D or multi-dimensional array of samples into overlapping windows.

    Yields:
      Tuple of (window_samples, window_start_time, window_start_sample_index)
    """
    if config is None:
        config = WindowConfig()

    arr = np.asarray(samples)
    total_samples = arr.shape[-1]

    if total_samples < config.window_size:
        return

    taper = config.get_taper_window() if apply_taper else None
    start_idx = 0

    while start_idx + config.window_size <= total_samples:
        if arr.ndim == 1:
            window = arr[start_idx : start_idx + config.window_size].astype(np.float64)
            if taper is not None:
                window = window * taper
        else:
            # Multi-channel array shape (C, N)
            window = arr[..., start_idx : start_idx + config.window_size].astype(np.float64)
            if taper is not None:
                window = window * taper[np.newaxis, :]

        window_time = None
        if start_timestamp is not None and sample_rate_hz > 0:
            offset_seconds = start_idx / sample_rate_hz
            window_time = start_timestamp + timedelta(seconds=offset_seconds)

        yield window, window_time, start_idx
        start_idx += config.step_size
