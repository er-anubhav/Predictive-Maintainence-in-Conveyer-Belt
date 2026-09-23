import pytest
import numpy as np
from ml.signal_processing.frequency_features import calculate_frequency_features


def test_dominant_frequency_pure_sine():
    """
    Pure 50.0 Hz sine wave sampled at 1000 Hz for 1000 samples.
    FFT frequency resolution is exactly 1.0 Hz per bin.
    Dominant frequency should be exactly 50.0 Hz.
    """
    fs = 1000.0
    f0 = 50.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    sine = 2.0 * np.sin(2 * np.pi * f0 * t)

    feats = calculate_frequency_features(sine, sample_rate_hz=fs)

    assert np.isclose(feats.dominant_frequency_hz, 50.0, atol=0.5)
    # Spectral centroid should also be near 50 Hz
    assert np.isclose(feats.spectral_centroid_hz, 50.0, atol=1.0)
    # 50 Hz belongs to the 50_100hz band
    assert feats.band_energy["50_100hz"] > 0
    assert feats.band_energy["100_250hz"] == 0.0


def test_spectral_entropy_comparison():
    """
    Single frequency pure tone has concentrated spectrum (low entropy).
    Gaussian white noise has flat, uniformly dispersed spectrum (high entropy).
    """
    fs = 1000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    pure_tone = np.sin(2 * np.pi * 75.0 * t)

    rng = np.random.default_rng(789)
    white_noise = rng.normal(0, 1.0, size=int(fs))

    tone_feats = calculate_frequency_features(pure_tone, sample_rate_hz=fs)
    noise_feats = calculate_frequency_features(white_noise, sample_rate_hz=fs)

    assert tone_feats.spectral_entropy < 0.20, f"Expected low entropy for tone, got {tone_feats.spectral_entropy}"
    assert noise_feats.spectral_entropy > 0.85, f"Expected high entropy for noise, got {noise_feats.spectral_entropy}"


def test_configurable_bands():
    fs = 1000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    # Signal with 25 Hz and 200 Hz
    sig = np.sin(2 * np.pi * 25.0 * t) + np.sin(2 * np.pi * 200.0 * t)

    custom_bands = {
        "sub_50": (0.0, 50.0),
        "mid_50_150": (50.0, 150.0),
        "high_150_300": (150.0, 300.0),
    }
    feats = calculate_frequency_features(sig, sample_rate_hz=fs, bands=custom_bands)

    assert feats.band_energy["sub_50"] > 0.0
    assert feats.band_energy["high_150_300"] > 0.0
    assert feats.band_energy["mid_50_150"] == 0.0


def test_invalid_fft_parameters():
    with pytest.raises(ValueError, match="Insufficient samples"):
        calculate_frequency_features(np.array([1.0, 2.0]))

    with pytest.raises(ValueError, match="Sample rate must be positive"):
        calculate_frequency_features(np.ones(64), sample_rate_hz=-10.0)
