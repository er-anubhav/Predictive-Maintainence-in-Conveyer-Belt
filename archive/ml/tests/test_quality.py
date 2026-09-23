import numpy as np
from ml.signal_processing.quality import check_signal_quality, SignalQualityAuditor


def test_quality_clean_signal():
    t = np.linspace(0, 1.0, 1024, endpoint=False)
    sine = 1.5 * np.sin(2 * np.pi * 20.0 * t) + np.random.normal(0, 0.1, 1024)

    res = check_signal_quality(sine, sample_rate_hz=1000.0)
    assert res.valid is True
    assert res.quality_score >= 0.95
    assert len(res.issues) == 0


def test_quality_empty_and_none():
    res_empty = check_signal_quality([])
    assert res_empty.valid is False
    assert res_empty.quality_score == 0.0
    assert "EMPTY_SIGNAL" in res_empty.issues

    res_none = check_signal_quality(None)
    assert res_none.valid is False
    assert res_none.quality_score == 0.0
    assert "EMPTY_SIGNAL_NONE" in res_none.issues


def test_quality_nan_and_inf():
    arr_nan = np.ones(100)
    arr_nan[50] = np.nan
    res_nan = check_signal_quality(arr_nan)
    assert res_nan.valid is False
    assert "NAN_VALUES_DETECTED" in res_nan.issues

    arr_inf = np.ones(100)
    arr_inf[20] = np.inf
    res_inf = check_signal_quality(arr_inf)
    assert res_inf.valid is False
    assert "INFINITE_VALUES_DETECTED" in res_inf.issues


def test_quality_flatline_sensor_disconnected():
    # Perfectly flat or constant sensor voltage
    arr_flat = np.full(500, 2.5)
    res_flat = check_signal_quality(arr_flat)
    assert res_flat.valid is False
    assert "FLATLINE_SENSOR_DISCONNECTED" in res_flat.issues


def test_quality_clipping_detection():
    # Signal that hits ±16g rail repeatedly
    arr = np.random.normal(0, 5.0, 1000)
    # 3% of samples pegged to rail
    arr[0:30] = 16.5
    auditor = SignalQualityAuditor(clipping_threshold=16.0, clipping_ratio_threshold=0.01)
    res = auditor.audit(arr)

    assert any("CLIPPING_SATURATION_DETECTED" in issue for issue in res.issues)
    assert res.quality_score < 1.0


def test_quality_impossible_sample_rate():
    arr = np.random.normal(0, 1.0, 100)
    res = check_signal_quality(arr, sample_rate_hz=-100)
    assert res.valid is False
    assert "IMPOSSIBLE_SAMPLE_RATE_NON_POSITIVE" in res.issues
