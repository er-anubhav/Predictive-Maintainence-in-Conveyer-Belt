import pytest
import numpy as np
from ml.signal_processing.filtering import (
    remove_dc,
    detrend_signal,
    apply_butterworth_filter,
    validate_filter_frequencies,
)


def test_remove_dc():
    # Signal with known DC offset of +5.0
    t = np.linspace(0, 1.0, 1000, endpoint=False)
    sine = np.sin(2 * np.pi * 10 * t)
    biased_signal = sine + 5.0

    clean = remove_dc(biased_signal)
    assert np.isclose(np.mean(clean), 0.0, atol=1e-6)
    # AC amplitude preserved
    assert np.isclose(np.max(clean) - np.min(clean), 2.0, atol=1e-3)


def test_detrend_linear():
    # Signal with linear drift + sine
    t = np.linspace(0, 1.0, 1000, endpoint=False)
    drift = 3.5 * t
    sine = np.sin(2 * np.pi * 5 * t)
    drifting_signal = sine + drift

    detrended = detrend_signal(drifting_signal, trend_type="linear")
    # Linear slope is eliminated to machine precision
    slope, intercept = np.polyfit(t, detrended, 1)
    assert np.isclose(slope, 0.0, atol=1e-12)


def test_butterworth_lowpass_attenuation():
    # Signal containing low frequency (10 Hz) and high frequency (150 Hz)
    fs = 1000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    low_freq = 1.0 * np.sin(2 * np.pi * 10.0 * t)
    high_freq = 1.0 * np.sin(2 * np.pi * 150.0 * t)
    combined = low_freq + high_freq

    # Low-pass filter at 30 Hz (should eliminate 150 Hz)
    filtered = apply_butterworth_filter(
        combined,
        sample_rate_hz=fs,
        cutoff_hz=30.0,
        filter_type="lowpass",
        order=4,
    )

    # Output matches the 10 Hz sine wave closely
    assert np.isclose(np.std(filtered), 1.0 / np.sqrt(2), rtol=0.15)
    # Away from filter edge padding transients, 150 Hz is attenuated by > 60 dB
    residual = filtered[100:-100] - low_freq[100:-100]
    assert np.max(np.abs(residual)) < 0.01


def test_butterworth_bandpass():
    fs = 1000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    f1, f2, f3 = 5.0, 50.0, 300.0
    sig = (
        1.0 * np.sin(2 * np.pi * f1 * t)
        + 1.0 * np.sin(2 * np.pi * f2 * t)
        + 1.0 * np.sin(2 * np.pi * f3 * t)
    )

    # Pass 30 Hz - 100 Hz (keeps f2=50 Hz, rejects f1 and f3)
    filtered = apply_butterworth_filter(
        sig,
        sample_rate_hz=fs,
        cutoff_hz=(30.0, 100.0),
        filter_type="bandpass",
        order=4,
    )

    # Center component preserved
    f2_expected = 1.0 * np.sin(2 * np.pi * f2 * t)
    correlation = np.corrcoef(filtered, f2_expected)[0, 1]
    assert correlation > 0.95


def test_nyquist_constraint_violations():
    fs = 1000.0  # Nyquist = 500 Hz

    # Cutoff above Nyquist
    with pytest.raises(ValueError, match="strictly less than Nyquist"):
        validate_filter_frequencies(fs, cutoff_hz=500.0, filter_type="lowpass")

    with pytest.raises(ValueError, match="strictly less than Nyquist"):
        validate_filter_frequencies(fs, cutoff_hz=600.0, filter_type="lowpass")

    # Inverted bandpass
    with pytest.raises(ValueError, match="strictly less than higher cutoff"):
        validate_filter_frequencies(fs, cutoff_hz=(200.0, 100.0), filter_type="bandpass")

    # Negative cutoff
    with pytest.raises(ValueError, match="strictly positive"):
        validate_filter_frequencies(fs, cutoff_hz=-10.0, filter_type="lowpass")
