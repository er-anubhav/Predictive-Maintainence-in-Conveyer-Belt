from typing import Dict, Any, Union
import numpy as np
from scipy import stats
from ml.schemas.signal import TimeDomainFeatures


def calculate_time_features(samples: np.ndarray) -> TimeDomainFeatures:
    """
    Computes statistical and mechanical time-domain indicators from a 1D sample array.
    """
    arr = np.asarray(samples, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("Cannot calculate time-domain features on empty array.")

    n = len(arr)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    var_val = float(np.var(arr, ddof=1)) if n > 1 else 0.0
    rms_val = float(np.sqrt(np.mean(arr**2)))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    p2p_val = float(max_val - min_val)
    peak_val = float(np.max(np.abs(arr)))

    # Crest Factor = Absolute Peak / RMS
    crest_factor = float(peak_val / (rms_val + 1e-12)) if rms_val > 1e-9 else 0.0

    # Skewness (Fisher-Pearson coefficient of asymmetry)
    if std_val > 1e-9 and n > 2:
        skew_val = float(stats.skew(arr, bias=False))
    else:
        skew_val = 0.0

    # Kurtosis (Pearson kurtosis where normal distribution = 3.0)
    # Using fisher=False so normal = 3.0, pure sinusoid = 1.5
    if std_val > 1e-9 and n > 3:
        kurt_val = float(stats.kurtosis(arr, fisher=False, bias=False))
    else:
        kurt_val = 3.0

    return TimeDomainFeatures(
        mean=round(mean_val, 6),
        std=round(std_val, 6),
        var=round(var_val, 6),
        rms=round(rms_val, 6),
        min=round(min_val, 6),
        max=round(max_val, 6),
        peak_to_peak=round(p2p_val, 6),
        peak=round(peak_val, 6),
        crest_factor=round(crest_factor, 4),
        skewness=round(skew_val, 4),
        kurtosis=round(kurt_val, 4),
    )
