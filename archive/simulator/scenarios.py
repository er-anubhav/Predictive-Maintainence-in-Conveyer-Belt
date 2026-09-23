import math
import random
from typing import Dict, Any


class BaseScenario:
    """Base scenario generator with common random variation utilities."""

    def __init__(self, seed: int = None):
        self.rng = random.Random(seed)

    def jitter(self, base: float, spread: float) -> float:
        return round(base + self.rng.uniform(-spread, spread), 3)


class NormalScenario(BaseScenario):
    """
    Scenario 1: Normal Operational Regime
    Produces healthy, stable telemetry with typical operational noise and natural variations.
    """

    def generate(self, step: int) -> Dict[str, float]:
        # Subtle harmonic load variations
        load_cycle = math.sin(step * 0.1) * 3.0
        load = max(0.0, min(100.0, self.jitter(71.0 + load_cycle, 2.0)))

        # Belt speed slightly modulated by load
        belt_speed = self.jitter(2.80, 0.03)

        # Healthy vibration baseline
        vibration_rms = self.jitter(0.40, 0.03)
        vibration_peak = self.jitter(1.18, 0.08)
        vibration_kurtosis = self.jitter(3.02, 0.12)  # Gaussian standard

        # Acoustic emissions baseline
        acoustic_rms = self.jitter(0.28, 0.02)

        # Thermal equilibrium
        temperature = self.jitter(42.5, 0.8)

        # Tracking centered with minimal sway
        tracking_position = self.jitter(math.sin(step * 0.15) * 1.2, 0.4)

        return {
            "vibration_rms": max(0.01, vibration_rms),
            "vibration_peak": max(0.05, vibration_peak),
            "vibration_kurtosis": max(1.5, vibration_kurtosis),
            "acoustic_rms": max(0.01, acoustic_rms),
            "temperature": round(temperature, 2),
            "belt_speed": max(0.0, belt_speed),
            "load": round(load, 1),
            "tracking_position": round(tracking_position, 2),
        }


class MisalignmentScenario(BaseScenario):
    """
    Scenario 2: Conveyor Belt Misalignment / Edge Drift
    Gradually drifts the tracking position laterally, inducing side-edge rubbing,
    elevated acoustic friction noise, and increased vibration.
    """

    def generate(self, step: int) -> Dict[str, float]:
        # Progress factor from 0.0 to 1.0 (reaches severe misalignment after ~40 steps)
        progress = min(1.0, step / 40.0)

        # Lateral deviation builds from 0 mm to ~16.5 mm
        tracking_drift = (progress * 15.0) + math.sin(step * 0.2) * 1.8
        tracking_position = self.jitter(tracking_drift, 0.5)

        # Edge rubbing raises acoustic emission
        acoustic_rms = self.jitter(0.28 + (progress * 0.85), 0.05)

        # Vibration increases due to uneven roller flange friction
        vibration_rms = self.jitter(0.40 + (progress * 1.20), 0.06)
        vibration_peak = self.jitter(1.20 + (progress * 1.30), 0.12)
        vibration_kurtosis = self.jitter(3.05 + (progress * 0.45), 0.15)

        # Moderate friction thermal heating
        temperature = self.jitter(42.5 + (progress * 11.0), 0.7)

        belt_speed = self.jitter(2.80 - (progress * 0.15), 0.04)
        load = self.jitter(72.0, 2.5)

        return {
            "vibration_rms": round(max(0.01, vibration_rms), 3),
            "vibration_peak": round(max(0.05, vibration_peak), 3),
            "vibration_kurtosis": round(max(1.5, vibration_kurtosis), 3),
            "acoustic_rms": round(max(0.01, acoustic_rms), 3),
            "temperature": round(temperature, 2),
            "belt_speed": round(max(0.0, belt_speed), 2),
            "load": round(max(0.0, min(100.0, load)), 1),
            "tracking_position": round(tracking_position, 2),
        }


class MechanicalAbnormalityScenario(BaseScenario):
    """
    Scenario 3: Mechanical Abnormality (Bearing Pitting, Roller Seizure & Splice Damage)
    Simulates high-impact shocks (elevated kurtosis and peak vibration),
    rapidly climbing vibration RMS, loud acoustic emission, and thermal runaway.
    """

    def generate(self, step: int) -> Dict[str, float]:
        # Progress factor reaching critical state after ~35 steps
        progress = min(1.0, step / 35.0)

        # Severe impulsive vibration: kurtosis rises towards 6.5 - 8.0
        vibration_kurtosis = self.jitter(3.0 + (progress * 4.5), 0.35)
        # Periodic impact shock pulses
        shock = 1.8 if (step % 4 == 0) else 0.0
        vibration_peak = self.jitter(1.20 + (progress * 3.2) + shock, 0.25)
        vibration_rms = self.jitter(0.40 + (progress * 2.8), 0.12)

        # High frequency acoustic emissions from metal-on-metal bearing fatigue
        acoustic_rms = self.jitter(0.28 + (progress * 1.60), 0.08)

        # Friction-induced bearing overheating (42.5°C -> 76°C)
        temperature = self.jitter(42.5 + (progress * 34.0), 1.0)

        # Minor tracking deviation under bearing binding
        tracking_position = self.jitter(-2.5 - (progress * 3.5), 0.7)

        # Conveyor drive experiences slight load drag
        load = self.jitter(72.0 + (progress * 12.0), 2.0)
        belt_speed = self.jitter(2.80 - (progress * 0.25), 0.05)

        return {
            "vibration_rms": round(max(0.01, vibration_rms), 3),
            "vibration_peak": round(max(0.05, vibration_peak), 3),
            "vibration_kurtosis": round(max(1.5, vibration_kurtosis), 3),
            "acoustic_rms": round(max(0.01, acoustic_rms), 3),
            "temperature": round(temperature, 2),
            "belt_speed": round(max(0.0, belt_speed), 2),
            "load": round(max(0.0, min(100.0, load)), 1),
            "tracking_position": round(tracking_position, 2),
        }


SCENARIOS = {
    "normal": NormalScenario,
    "misalignment": MisalignmentScenario,
    "mechanical_abnormality": MechanicalAbnormalityScenario,
    "mechanical_impulse": MechanicalAbnormalityScenario,
    "imbalance": MechanicalAbnormalityScenario,
    "noisy_sensor": NormalScenario,
}


def get_scenario(name: str) -> BaseScenario:
    scenario_cls = SCENARIOS.get(name.lower())
    if not scenario_cls:
        valid = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{name}'. Valid choices: {valid}")
    return scenario_cls()
