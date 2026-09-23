from typing import Union, Tuple, Optional
import numpy as np
from scipy import signal as sp_signal


def remove_dc(samples: np.ndarray) -> np.ndarray:
    """Subtracts the arithmetic mean (DC bias) from the sample series."""
    arr = np.asarray(samples, dtype=np.float64)
    if arr.ndim == 1:
        return arr - np.mean(arr)
    return arr - np.mean(arr, axis=-1, keepdims=True)


def detrend_signal(samples: np.ndarray, trend_type: str = "linear") -> np.ndarray:
    """
    Detrends the signal by removing linear or constant trends.
    trend_type: 'linear' or 'constant'
    """
    arr = np.asarray(samples, dtype=np.float64)
    if trend_type not in ("linear", "constant"):
        raise ValueError(f"Invalid trend_type '{trend_type}'. Must be 'linear' or 'constant'.")
    return sp_signal.detrend(arr, type=trend_type, axis=-1)


def validate_filter_frequencies(
    sample_rate_hz: float,
    cutoff_hz: Union[float, Tuple[float, float]],
    filter_type: str,
) -> None:
    """Validates filter cutoff frequencies against sampling rate and Nyquist limit."""
    if sample_rate_hz <= 0:
        raise ValueError(f"Sample rate must be positive, got {sample_rate_hz} Hz")

    nyquist = sample_rate_hz / 2.0

    if filter_type in ("lowpass", "highpass"):
        if not isinstance(cutoff_hz, (int, float)):
            raise ValueError(f"Cutoff frequency must be a scalar float for {filter_type}, got {cutoff_hz}")
        if cutoff_hz <= 0:
            raise ValueError(f"Cutoff frequency must be strictly positive, got {cutoff_hz} Hz")
        if cutoff_hz >= nyquist:
            raise ValueError(
                f"Cutoff frequency {cutoff_hz} Hz must be strictly less than Nyquist frequency {nyquist} Hz"
            )

    elif filter_type in ("bandpass", "bandstop"):
        if not (isinstance(cutoff_hz, (tuple, list)) and len(cutoff_hz) == 2):
            raise ValueError(
                f"Cutoff frequencies must be a 2-element tuple/list (low, high) for {filter_type}, got {cutoff_hz}"
            )
        low, high = float(cutoff_hz[0]), float(cutoff_hz[1])
        if low <= 0:
            raise ValueError(f"Lower cutoff frequency must be positive, got {low} Hz")
        if low >= high:
            raise ValueError(f"Lower cutoff {low} Hz must be strictly less than higher cutoff {high} Hz")
        if high >= nyquist:
            raise ValueError(
                f"Higher cutoff frequency {high} Hz must be strictly less than Nyquist frequency {nyquist} Hz"
            )
    else:
        raise ValueError(f"Unsupported filter_type: {filter_type}. Expected lowpass, highpass, bandpass, bandstop.")


def apply_butterworth_filter(
    samples: np.ndarray,
    sample_rate_hz: float,
    cutoff_hz: Union[float, Tuple[float, float]],
    filter_type: str = "bandpass",
    order: int = 4,
) -> np.ndarray:
    """
    Applies a zero-phase Butterworth filter using Second-Order Sections (SOS) for numerical stability.
    """
    validate_filter_frequencies(sample_rate_hz, cutoff_hz, filter_type)

    if order <= 0 or order > 12:
        raise ValueError(f"Filter order must be between 1 and 12, got {order}")

    arr = np.asarray(samples, dtype=np.float64)
    if arr.size == 0:
        return arr

    # Calculate second-order sections (SOS) representation
    sos = sp_signal.butter(
        N=order,
        Wn=cutoff_hz,
        btype=filter_type,
        analog=False,
        output="sos",
        fs=sample_rate_hz,
    )

    # Zero-phase forward-backward filtering
    return sp_signal.sosfiltfilt(sos, arr, axis=-1)
