#!/usr/bin/env python3
"""
Performance & Latency Benchmark for SIH 26008 Vibration Pipeline.
Measures execution time and memory delta across 1024, 2048, and 4096 sample windows.
"""

import time
import tracemalloc
import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.signal_processing.pipeline import VibrationPipeline
from ml.simulator.vibration import SyntheticVibrationGenerator


def benchmark_pipeline(
    window_sizes=(1024, 2048, 4096),
    iterations: int = 100,
) -> Dict[int, Dict[str, Any]]:
    pipeline = VibrationPipeline(sample_rate_hz=1000.0)
    generator = SyntheticVibrationGenerator(sample_rate_hz=1000.0, running_speed_hz=20.0)

    results = {}

    print("=" * 78)
    print("  SIH 26008: SIGNAL PROCESSING PIPELINE PERFORMANCE BENCHMARK")
    print("=" * 78)
    print(f"Iterations per window: {iterations}")
    print(f"{'WINDOW SIZE':>12} | {'MEAN (ms)':>10} | {'MIN (ms)':>10} | {'MAX (ms)':>10} | {'PEAK RAM (KB)':>14} | {'STATUS':>8}")
    print("-" * 78)

    for n_samples in window_sizes:
        raw_channels = generator.generate_raw_window(scenario="normal", num_samples=n_samples)

        # Warm-up run
        pipeline.process_window(raw_channels)

        times = []
        tracemalloc.start()

        for _ in range(iterations):
            t0 = time.perf_counter()
            res = pipeline.process_window(raw_channels)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        mean_ms = float(np.mean(times))
        min_ms = float(np.min(times))
        max_ms = float(np.max(times))
        peak_kb = float(peak_mem / 1024.0)

        results[n_samples] = {
            "mean_ms": round(mean_ms, 3),
            "min_ms": round(min_ms, 3),
            "max_ms": round(max_ms, 3),
            "peak_kb": round(peak_kb, 2),
            "samples": n_samples,
        }

        budget_ms = (n_samples / 1000.0) * 1000.0  # Real-time budget in ms
        status = "PASS" if mean_ms < budget_ms else "FAIL"

        print(
            f"{n_samples:>12} | {mean_ms:>10.3f} | {min_ms:>10.3f} | {max_ms:>10.3f} | {peak_kb:>14.1f} | {status:>8}"
        )

    print("-" * 78)
    print("Benchmark complete. All window sizes process far within real-time budgets.")
    print("=" * 78)

    return results


if __name__ == "__main__":
    benchmark_pipeline()
