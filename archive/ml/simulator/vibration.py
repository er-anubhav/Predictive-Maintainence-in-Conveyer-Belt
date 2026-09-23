"""
Synthetic Raw Vibration Signal Generator for SIH 26008.

NOTE: These are deterministic simulation scenarios designed to validate
signal processing, filtering, and feature extraction algorithms. They are not
claims about exact real-world fault signatures of specific conveyor hardware.
"""

from typing import Dict, Tuple, Optional
import numpy as np


class SyntheticVibrationGenerator:
    """
    Generates synthetic raw tri-axial (X, Y, Z) accelerometer time series at a specified sampling rate.
    Default sampling rate: 1000 Hz.
    """

    def __init__(
        self,
        sample_rate_hz: float = 1000.0,
        running_speed_hz: float = 20.0,  # ~1200 RPM drive pulley shaft speed
        random_seed: Optional[int] = 42,
    ):
        self.sample_rate_hz = sample_rate_hz
        self.running_speed_hz = running_speed_hz
        self.rng = np.random.default_rng(random_seed)

    def generate_raw_window(
        self,
        scenario: str = "normal",
        num_samples: int = 1024,
        time_offset: float = 0.0,
    ) -> Dict[str, np.ndarray]:
        """
        Generates a 3-channel (x, y, z) raw sample window of length num_samples.
        """
        t = time_offset + np.arange(num_samples) / self.sample_rate_hz
        f0 = self.running_speed_hz

        if scenario == "normal":
            # Normal: Low amplitude baseline vibration, fundamental + 2nd harmonic, low noise
            x = (
                0.25 * np.sin(2 * np.pi * f0 * t)
                + 0.08 * np.sin(2 * np.pi * 2 * f0 * t)
                + self.rng.normal(0, 0.05, num_samples)
            )
            y = (
                0.15 * np.sin(2 * np.pi * f0 * t + np.pi / 4)
                + self.rng.normal(0, 0.04, num_samples)
            )
            z = (
                0.30 * np.sin(2 * np.pi * f0 * t + np.pi / 2)
                + 0.05 * np.sin(2 * np.pi * 3 * f0 * t)
                + self.rng.normal(0, 0.05, num_samples)
            )

        elif scenario == "misalignment":
            # Misalignment: Strong 2x running speed harmonic (coupling/pulley alignment), elevated Y/Z lateral vibration
            x = (
                0.40 * np.sin(2 * np.pi * f0 * t)
                + 0.65 * np.sin(2 * np.pi * 2 * f0 * t)
                + 0.20 * np.sin(2 * np.pi * 3 * f0 * t)
                + self.rng.normal(0, 0.08, num_samples)
            )
            y = (
                0.80 * np.sin(2 * np.pi * 2 * f0 * t + np.pi / 3)
                + 0.35 * np.sin(2 * np.pi * f0 * t)
                + self.rng.normal(0, 0.08, num_samples)
            )
            z = (
                0.50 * np.sin(2 * np.pi * f0 * t)
                + 0.55 * np.sin(2 * np.pi * 2 * f0 * t)
                + self.rng.normal(0, 0.08, num_samples)
            )

        elif scenario == "imbalance":
            # Imbalance: Pronounced sinusoidal 1x running speed component in radial axes (X and Z)
            x = (
                1.40 * np.sin(2 * np.pi * f0 * t)
                + 0.15 * np.sin(2 * np.pi * 2 * f0 * t)
                + self.rng.normal(0, 0.06, num_samples)
            )
            y = (
                0.25 * np.sin(2 * np.pi * f0 * t)
                + self.rng.normal(0, 0.05, num_samples)
            )
            z = (
                1.30 * np.sin(2 * np.pi * f0 * t + np.pi / 2)
                + 0.12 * np.sin(2 * np.pi * 2 * f0 * t)
                + self.rng.normal(0, 0.06, num_samples)
            )

        elif scenario == "mechanical_impulse":
            # Mechanical impulse: Baseline running speed + repetitive decaying exponential shocks (e.g. cracked roller / joint splice slap)
            # Produces high kurtosis (> 5.0) and high crest factor (> 4.0)
            base_x = 0.30 * np.sin(2 * np.pi * f0 * t) + self.rng.normal(0, 0.05, num_samples)
            base_y = 0.20 * np.sin(2 * np.pi * f0 * t) + self.rng.normal(0, 0.04, num_samples)
            base_z = 0.25 * np.sin(2 * np.pi * f0 * t) + self.rng.normal(0, 0.05, num_samples)

            # Insert damped impulses every ~0.25 seconds (4 Hz repetition rate)
            impulse_period = int(self.sample_rate_hz / 4)
            damped_decay = np.exp(-np.linspace(0, 10, min(80, impulse_period)))
            high_freq_ring = np.sin(2 * np.pi * 180.0 * np.arange(len(damped_decay)) / self.sample_rate_hz)
            transient = 2.8 * damped_decay * high_freq_ring

            for idx in range(impulse_period // 2, num_samples - len(transient), impulse_period):
                base_x[idx : idx + len(transient)] += transient
                base_z[idx : idx + len(transient)] += transient * 0.7

            x, y, z = base_x, base_y, base_z

        elif scenario == "noisy_sensor":
            # Noisy sensor: High white noise floor with occasional rail clipping saturation (±16g rail)
            noise_x = self.rng.normal(0, 3.5, num_samples)
            noise_y = self.rng.normal(0, 3.0, num_samples)
            noise_z = self.rng.normal(0, 3.5, num_samples)

            # Artificially inject clipping at ±16.0g on ~2% of samples
            clip_indices = self.rng.choice(num_samples, size=int(num_samples * 0.02), replace=False)
            noise_x[clip_indices] = 16.2 * np.sign(self.rng.normal(0, 1, len(clip_indices)))
            x, y, z = noise_x, noise_y, noise_z

        else:
            raise ValueError(f"Unknown scenario '{scenario}'. Supported: normal, misalignment, imbalance, mechanical_impulse, noisy_sensor.")

        return {
            "x": np.round(x, 4),
            "y": np.round(y, 4),
            "z": np.round(z, 4),
        }
