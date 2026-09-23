#!/usr/bin/env python3
"""
Telemetry Data Generator CLI for SIH 26008:
Intelligent Conveyor Belt Health & Predictive Maintenance.

Supports Dual-Transport:
1. --transport direct   -> FastAPI backend (http://localhost:8000/api/v1/telemetry)
2. --transport gateway  -> Edge Gateway agent (http://localhost:9000/ingest) with canonical schema
"""

import argparse
from datetime import datetime, timezone
import os
import pathlib
import signal
import sys
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scenarios import get_scenario, SCENARIOS
from sender import TelemetrySender

RUNNING = True


def handle_signal(sig, frame):
    global RUNNING
    print("\n[!] Received interrupt signal. Stopping simulator cleanly...")
    RUNNING = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def main():
    parser = argparse.ArgumentParser(
        description="Simulate conveyor belt multi-modal edge sensor telemetry (Direct or Gateway transport)."
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="direct",
        choices=["direct", "gateway"],
        help="Transport destination: 'direct' (FastAPI :8000) or 'gateway' (Edge Gateway :9000) (default: direct)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        choices=list(SCENARIOS.keys()),
        help=f"Fault simulation scenario: {', '.join(SCENARIOS.keys())} (default: normal)",
    )
    parser.add_argument(
        "--sensor-node-id",
        "--node-id",
        dest="sensor_node_id",
        type=str,
        default="NODE-001",
        help="Target sensor node code (default: NODE-001)",
    )
    parser.add_argument(
        "--conveyor-id",
        type=str,
        default="Conveyor-01",
        help="Associated conveyor name or ID (default: Conveyor-01)",
    )
    parser.add_argument(
        "--start-sequence",
        type=int,
        default=1001,
        help="Initial monotonic sequence number (default: 1001)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Sampling and transmission interval in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Custom destination URL (defaults to :8000 for direct or :9000 for gateway)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of packets to transmit before exiting (default: infinite)",
    )
    parser.add_argument(
        "--signal-processing",
        action="store_true",
        help="Enable edge signal processing pipeline (transforms raw synthetic vibration into time/frequency features)",
    )

    args = parser.parse_args()

    # Determine default URL depending on transport mode
    if args.api_url:
        target_url = args.api_url
    elif args.transport == "gateway":
        target_url = os.getenv("GATEWAY_INGEST_URL", "http://localhost:9000/ingest")
    else:
        target_url = os.getenv("TELEMETRY_API_URL", "http://localhost:8000/api/v1/telemetry")

    scenario = get_scenario(args.scenario)
    sender = TelemetrySender(target_url=target_url)

    raw_gen = None
    pipeline = None
    if args.signal_processing:
        from ml.simulator.vibration import SyntheticVibrationGenerator
        from ml.signal_processing.pipeline import VibrationPipeline

        raw_gen = SyntheticVibrationGenerator(sample_rate_hz=1000.0, random_seed=42)
        pipeline = VibrationPipeline(sample_rate_hz=1000.0)

    print("=" * 78)
    print("  CONVEYOR BELT HEALTH TELEMETRY SIMULATOR — SIH 26008")
    print("=" * 78)
    print(f"  Transport Mode:    {args.transport.upper()} -> {target_url}")
    print(f"  Sensor Node ID:    {args.sensor_node_id}")
    print(f"  Conveyor ID:       {args.conveyor_id}")
    print(f"  Scenario:          {args.scenario.upper()}")
    print(f"  Signal Processing: {'ENABLED (1000 Hz, 1024-sample FFT/Filtering)' if args.signal_processing else 'DISABLED (Direct Metric Mode)'}")
    print(f"  Initial Sequence:  {args.start_sequence}")
    print(f"  Interval:          {args.interval}s")
    print(f"  Packet Count:      {'Continuous (Ctrl+C to stop)' if args.count is None else args.count}")
    print("=" * 78)
    if args.signal_processing:
        print(
            f"{'STEP':>4} | {'SEQ':>5} | {'TIMESTAMP':^20} | {'VIB RMS':>7} | {'PEAK':>5} | {'KURT':>4} | {'CREST':>5} | {'DOM FREQ':>9} | {'TEMP':>5} | STATUS"
        )
    else:
        print(
            f"{'STEP':>4} | {'SEQ':>5} | {'TIMESTAMP':^20} | {'VIB RMS':>7} | {'PEAK':>5} | {'KURT':>4} | {'TEMP':>5} | {'SPEED':>5} | {'TRACK':>6} | STATUS"
        )
    print("-" * 102)

    step = 0
    seq = args.start_sequence
    success_count = 0
    fail_count = 0

    while RUNNING:
        step += 1
        iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sample_metrics = scenario.generate(step)

        if args.signal_processing and pipeline and raw_gen:
            raw_scenario = args.scenario
            if raw_scenario == "mechanical_abnormality":
                raw_scenario = "mechanical_impulse"
            elif raw_scenario not in ["normal", "misalignment", "imbalance", "mechanical_impulse", "noisy_sensor"]:
                raw_scenario = "normal"

            raw_window = raw_gen.generate_raw_window(
                scenario=raw_scenario,
                num_samples=1024,
                time_offset=step * 1.024,
            )
            proc_result = pipeline.process_window(
                samples=raw_window,
                sample_rate_hz=1000.0,
                timestamp=iso_timestamp,
            )
            agg = proc_result.features.aggregate
            sample_metrics["vibration_rms"] = agg["vector_rms"]
            sample_metrics["vibration_peak"] = agg["vector_peak"]
            sample_metrics["vibration_kurtosis"] = agg["kurtosis"]
            sample_metrics["crest_factor"] = agg["crest_factor"]
            sample_metrics["dominant_frequency_hz"] = agg["dominant_frequency_hz"]
            sample_metrics["spectral_energy"] = agg["spectral_energy"]

        if args.transport == "gateway":
            # Canonical Telemetry Payload
            vib_block = {
                "rms": sample_metrics["vibration_rms"],
                "peak": sample_metrics["vibration_peak"],
                "kurtosis": sample_metrics["vibration_kurtosis"],
            }
            if "crest_factor" in sample_metrics:
                vib_block["crest_factor"] = sample_metrics["crest_factor"]
            if "dominant_frequency_hz" in sample_metrics:
                vib_block["dominant_frequency_hz"] = sample_metrics["dominant_frequency_hz"]
            if "spectral_energy" in sample_metrics:
                vib_block["spectral_energy"] = sample_metrics["spectral_energy"]

            payload = {
                "schema_version": "1.0",
                "node_id": args.sensor_node_id,
                "conveyor_id": args.conveyor_id,
                "timestamp": iso_timestamp,
                "sequence": seq,
                "vibration": vib_block,
                "acoustic": {
                    "rms": sample_metrics["acoustic_rms"],
                },
                "temperature": sample_metrics["temperature"],
                "belt_speed": sample_metrics["belt_speed"],
                "load": sample_metrics["load"],
                "tracking_position": sample_metrics["tracking_position"],
            }
        else:
            # Direct FastAPI Payload (Flat schema with sequence)
            payload = {
                "sensor_node_id": args.sensor_node_id,
                "sequence": seq,
                "timestamp": iso_timestamp,
                **sample_metrics,
            }

        sent, status_code, message = sender.send(payload)
        if sent:
            success_count += 1
            status_tag = f"OK ({status_code})"
        else:
            fail_count += 1
            status_tag = f"ERR ({status_code})"

        if args.signal_processing:
            print(
                f"{step:>4} | {seq:>5} | {iso_timestamp} | "
                f"{sample_metrics['vibration_rms']:>6.3f}g | "
                f"{sample_metrics['vibration_peak']:>4.2f}g | "
                f"{sample_metrics['vibration_kurtosis']:>4.2f} | "
                f"{sample_metrics.get('crest_factor', 0):>5.2f} | "
                f"{sample_metrics.get('dominant_frequency_hz', 0):>7.1f}Hz | "
                f"{sample_metrics['temperature']:>4.1f}C | {status_tag}"
            )
        else:
            print(
                f"{step:>4} | {seq:>5} | {iso_timestamp} | "
                f"{sample_metrics['vibration_rms']:>6.3f}g | "
                f"{sample_metrics['vibration_peak']:>4.2f}g | "
                f"{sample_metrics['vibration_kurtosis']:>4.2f} | "
                f"{sample_metrics['temperature']:>4.1f}C | "
                f"{sample_metrics['belt_speed']:>4.2f} | "
                f"{sample_metrics['tracking_position']:>+5.1f}mm | {status_tag}"
            )

        seq += 1

        if args.count is not None and step >= args.count:
            break

        if RUNNING:
            time.sleep(args.interval)

    print("-" * 96)
    print(f"[Done] Total steps: {step} | Delivered: {success_count} | Failed: {fail_count}")


if __name__ == "__main__":
    main()
