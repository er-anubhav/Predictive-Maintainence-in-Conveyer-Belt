from typing import Optional, List, Union
import numpy as np
from ml.schemas.signal import SignalQualityResult


class SignalQualityAuditor:
    """
    Evaluates sensor time-series integrity and flags hardware, transmission,
    or ADC quantization failures.
    """

    def __init__(
        self,
        min_samples: int = 32,
        flatline_std_threshold: float = 1e-6,
        clipping_threshold: float = 15.5,  # e.g. ±16g rail for typical accelerometer
        clipping_ratio_threshold: float = 0.01,  # >1% samples at rail
    ):
        self.min_samples = min_samples
        self.flatline_std_threshold = flatline_std_threshold
        self.clipping_threshold = clipping_threshold
        self.clipping_ratio_threshold = clipping_ratio_threshold

    def audit(
        self,
        samples: Union[List[float], np.ndarray],
        sample_rate_hz: float = 1000.0,
    ) -> SignalQualityResult:
        issues: List[str] = []
        score: float = 1.0

        if samples is None:
            return SignalQualityResult(valid=False, quality_score=0.0, issues=["EMPTY_SIGNAL_NONE"])

        arr = np.asarray(samples, dtype=np.float64)

        # 1. Empty Check
        if arr.size == 0:
            return SignalQualityResult(valid=False, quality_score=0.0, issues=["EMPTY_SIGNAL"])

        # 2. Sample Rate Feasibility
        if sample_rate_hz <= 0:
            issues.append("IMPOSSIBLE_SAMPLE_RATE_NON_POSITIVE")
            score -= 0.5
        elif sample_rate_hz > 500_000:  # > 500 kHz is absurd for this hardware class
            issues.append("IMPOSSIBLE_SAMPLE_RATE_EXCESSIVE")
            score -= 0.3

        # 3. NaN or Infinite Values Check
        has_nan = np.isnan(arr).any()
        has_inf = np.isinf(arr).any()
        if has_nan:
            issues.append("NAN_VALUES_DETECTED")
            score = 0.0
        if has_inf:
            issues.append("INFINITE_VALUES_DETECTED")
            score = 0.0

        if has_nan or has_inf:
            return SignalQualityResult(valid=False, quality_score=0.0, issues=issues)

        # 4. Insufficient Samples
        if len(arr) < self.min_samples:
            issues.append(f"INSUFFICIENT_SAMPLES_{len(arr)}_MIN_{self.min_samples}")
            score -= 0.4

        # 5. Constant / Flatline Disconnection Check
        std_val = float(np.std(arr))
        if std_val < self.flatline_std_threshold:
            issues.append("FLATLINE_SENSOR_DISCONNECTED")
            score -= 0.7

        # 6. Clipping / Saturation Check
        peak_val = float(np.max(np.abs(arr)))
        if peak_val >= self.clipping_threshold:
            # Check how many samples are near the rail
            rail_hits = np.sum(np.abs(arr) >= (self.clipping_threshold * 0.99))
            ratio = float(rail_hits / len(arr))
            if ratio >= self.clipping_ratio_threshold:
                issues.append(f"CLIPPING_SATURATION_DETECTED_{ratio * 100:.1f}PCT")
                score -= 0.35
            else:
                issues.append("PEAK_APPROACHING_RAIL")
                score -= 0.15

        # Final Score bounds
        final_score = max(0.0, min(1.0, score))
        # Valid only if no critical fatal issues and score >= 0.50
        fatal_issues = {
            "EMPTY_SIGNAL",
            "EMPTY_SIGNAL_NONE",
            "NAN_VALUES_DETECTED",
            "INFINITE_VALUES_DETECTED",
            "FLATLINE_SENSOR_DISCONNECTED",
            "IMPOSSIBLE_SAMPLE_RATE_NON_POSITIVE",
        }
        has_fatal = any(issue in fatal_issues for issue in issues)
        is_valid = (not has_fatal) and (final_score >= 0.50)

        return SignalQualityResult(
            valid=is_valid,
            quality_score=round(final_score, 3),
            issues=issues,
        )


default_quality_auditor = SignalQualityAuditor()


def check_signal_quality(
    samples: Union[List[float], np.ndarray],
    sample_rate_hz: float = 1000.0,
) -> SignalQualityResult:
    return default_quality_auditor.audit(samples, sample_rate_hz)
