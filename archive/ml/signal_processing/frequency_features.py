from typing import Dict, Optional, Tuple
import numpy as np
from ml.schemas.signal import FrequencyDomainFeatures


DEFAULT_FREQUENCY_BANDS = {
    "0_50hz": (0.0, 50.0),
    "50_100hz": (50.0, 100.0),
    "100_250hz": (100.0, 250.0),
    "250_500hz": (250.0, 500.0),
}


def calculate_frequency_features(
    samples: np.ndarray,
    sample_rate_hz: float = 1000.0,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
    exclude_dc: bool = True,
) -> FrequencyDomainFeatures:
    """
    Computes deterministic FFT-based spectral features.
    """
    arr = np.asarray(samples, dtype=np.float64)
    n = len(arr)
    if n < 4:
        raise ValueError(f"Insufficient samples for FFT calculation: {n} (minimum 4)")
    if sample_rate_hz <= 0:
        raise ValueError(f"Sample rate must be positive, got {sample_rate_hz}")

    if bands is None:
        bands = DEFAULT_FREQUENCY_BANDS

    # Real FFT calculation
    fft_vals = np.fft.rfft(arr)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)
    magnitudes = np.abs(fft_vals)

    # Power spectral estimate (squared magnitudes normalized by N)
    power = (magnitudes**2) / n
    total_energy = float(np.sum(power))

    # Dominant Frequency (highest spectral peak, skipping DC bin at index 0 if exclude_dc=True)
    if exclude_dc and len(magnitudes) > 1:
        dom_idx = int(np.argmax(magnitudes[1:]) + 1)
    else:
        dom_idx = int(np.argmax(magnitudes))
    dominant_frequency_hz = float(freqs[dom_idx])

    # Spectral Centroid: sum(f_k * P_k) / sum(P_k)
    # Exclude DC to reflect actual dynamic oscillations
    calc_slice = slice(1, None) if exclude_dc and len(freqs) > 1 else slice(0, None)
    f_slice = freqs[calc_slice]
    p_slice = power[calc_slice]
    sum_p = np.sum(p_slice)

    if sum_p > 1e-12:
        spectral_centroid = float(np.sum(f_slice * p_slice) / sum_p)
        # Spectral Bandwidth: sqrt( sum((f_k - centroid)^2 * P_k) / sum(P_k) )
        spectral_bandwidth = float(np.sqrt(np.sum(((f_slice - spectral_centroid) ** 2) * p_slice) / sum_p))
    else:
        spectral_centroid = 0.0
        spectral_bandwidth = 0.0

    # Spectral Entropy: normalized Shannon entropy of power distribution
    if sum_p > 1e-12 and len(p_slice) > 1:
        norm_p = p_slice / sum_p
        # Filter non-zero probabilities
        nonzero_p = norm_p[norm_p > 1e-15]
        raw_entropy = -np.sum(nonzero_p * np.log2(nonzero_p))
        max_entropy = np.log2(len(norm_p))
        spectral_entropy = float(raw_entropy / max_entropy) if max_entropy > 0 else 0.0
    else:
        spectral_entropy = 0.0

    # Configurable Frequency Band Energies
    band_energies: Dict[str, float] = {}
    for band_name, (low_f, high_f) in bands.items():
        mask = (freqs >= low_f) & (freqs < high_f)
        band_power = float(np.sum(power[mask])) if np.any(mask) else 0.0
        band_energies[band_name] = round(band_power, 4)

    return FrequencyDomainFeatures(
        dominant_frequency_hz=round(dominant_frequency_hz, 2),
        spectral_energy=round(total_energy, 4),
        spectral_centroid_hz=round(spectral_centroid, 2),
        spectral_bandwidth_hz=round(spectral_bandwidth, 2),
        spectral_entropy=round(spectral_entropy, 4),
        band_energy=band_energies,
    )
