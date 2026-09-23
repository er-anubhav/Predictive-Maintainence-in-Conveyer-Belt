import pytest
import numpy as np
from ml.signal_processing.time_features import calculate_time_features


def test_time_features_sine_wave():
    """
    Tests exact analytical properties of a pure sine wave:
      A * sin(2 * pi * f * t)
      RMS = A / sqrt(2)
      Peak = A
      Variance = A^2 / 2
      Crest Factor = sqrt(2) approx 1.4142
      Kurtosis (Pearson) = 1.50
    """
    A = 2.0
    f = 10.0
    fs = 1000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)  # Exactly 10 cycles
    sine = A * np.sin(2 * np.pi * f * t)

    feats = calculate_time_features(sine)

    expected_rms = A / np.sqrt(2)
    expected_var = (A**2) / 2.0
    expected_crest = np.sqrt(2)

    assert np.isclose(feats.rms, expected_rms, atol=1e-3)
    assert np.isclose(feats.peak, A, atol=1e-3)
    assert np.isclose(feats.var, expected_var, atol=1e-2)
    assert np.isclose(feats.crest_factor, expected_crest, atol=1e-3)
    assert np.isclose(feats.mean, 0.0, atol=1e-4)
    # Sine wave kurtosis is mathematically 1.5
    assert np.isclose(feats.kurtosis, 1.5, atol=0.05)


def test_time_features_gaussian_noise():
    """
    Gaussian noise has theoretical Pearson kurtosis of 3.0 and skewness of 0.0.
    """
    rng = np.random.default_rng(123)
    noise = rng.normal(0, 1.0, size=20000)

    feats = calculate_time_features(noise)

    assert np.isclose(feats.mean, 0.0, atol=0.05)
    assert np.isclose(feats.std, 1.0, atol=0.05)
    assert np.isclose(feats.skewness, 0.0, atol=0.08)
    # Pearson kurtosis for normal distribution is approximately 3.0
    assert np.isclose(feats.kurtosis, 3.0, atol=0.15)


def test_time_features_impulsive_signal():
    """
    Impulsive signal (rare high-amplitude spikes) produces high kurtosis (> 5.0)
    and elevated crest factor (> 4.0).
    """
    rng = np.random.default_rng(456)
    signal = rng.normal(0, 0.2, size=1024)
    # Inject high shock impulses
    signal[100] = 6.0
    signal[500] = -5.5
    signal[800] = 7.0

    feats = calculate_time_features(signal)

    assert feats.kurtosis > 10.0, f"Expected high kurtosis for shock impulses, got {feats.kurtosis}"
    assert feats.crest_factor > 4.0, f"Expected elevated crest factor, got {feats.crest_factor}"
    assert feats.peak >= 7.0


def test_time_features_empty_rejection():
    with pytest.raises(ValueError, match="Cannot calculate time-domain features on empty array"):
        calculate_time_features(np.array([]))
