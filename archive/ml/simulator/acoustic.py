"""
Synthetic Raw Acoustic Emission Signal Generator for SIH 26008.
"""

from typing import Optional
import numpy as np


class SyntheticAcousticGenerator:
    """
    Generates synthetic high-frequency acoustic emission (AE) sensor signals
    representing rubbing friction, idler roller bearing distress, or belt slippage.
    """

    def __init__(
        self,
        sample_rate_hz: float = 2000.0,
        random_seed: Optional[int] = 42,
    ):
        self.sample_rate_hz = sample_rate_hz
        self.rng = np.random.default_rng(random_seed)

    def generate_raw_window(
        self,
        scenario: str = "normal",
        num_samples: int = 1024,
        time_offset: float = 0.0,
    ) -> np.ndarray:
        t = time_offset + np.arange(num_samples) / self.sample_rate_hz

        if scenario == "normal":
            # Normal background baseline acoustic noise
            signal = self.rng.normal(0, 0.15, num_samples)
        elif scenario in ("misalignment", "friction"):
            # Continuous rubbing friction (higher variance + periodic modulation)
            modulation = 0.5 * (1.0 + np.sin(2 * np.pi * 2.8 * t))  # Belt traversal rate
            friction_noise = self.rng.normal(0, 0.45, num_samples) * (1.0 + modulation)
            signal = friction_noise
        elif scenario == "mechanical_impulse":
            # Acoustic bursts from metal-on-metal impacts / roller cracks
            base = self.rng.normal(0, 0.18, num_samples)
            burst_period = int(self.sample_rate_hz / 4)
            decay = np.exp(-np.linspace(0, 15, 60))
            hf_carrier = np.sin(2 * np.pi * 450.0 * np.arange(60) / self.sample_rate_hz)
            burst = 1.8 * decay * hf_carrier

            for idx in range(burst_period // 2, num_samples - len(burst), burst_period):
                base[idx : idx + len(burst)] += burst
            signal = base
        else:
            signal = self.rng.normal(0, 0.20, num_samples)

        return np.round(signal, 4)
