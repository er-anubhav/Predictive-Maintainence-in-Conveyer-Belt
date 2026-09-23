from datetime import datetime, timezone
import numpy as np
from ml.signal_processing.windowing import WindowConfig, slice_windows
from ml.signal_processing.pipeline import VibrationPipeline
from ml.simulator.vibration import SyntheticVibrationGenerator
from ml.simulator.acoustic import SyntheticAcousticGenerator


def test_windowing_slice_counts_and_timestamps():
    total_samples = 2500
    arr = np.arange(total_samples)
    start_time = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    config = WindowConfig(window_size=1024, overlap=0.50)  # step = 512

    # Windows will be:
    # 1: [0 : 1024]
    # 2: [512 : 1536]
    # 3: [1024 : 2048]
    # (next start at 1536 + 1024 = 2560 > 2500, so stopped) -> exactly 3 windows
    windows = list(slice_windows(arr, sample_rate_hz=1000.0, start_timestamp=start_time, config=config))

    assert len(windows) == 3
    # Check start indices
    assert windows[0][2] == 0
    assert windows[1][2] == 512
    assert windows[2][2] == 1024

    # Check timestamps: 512 samples at 1000 Hz = 0.512 seconds
    assert windows[0][1] == start_time
    assert windows[1][1] == datetime(2026, 9, 21, 12, 0, 0, 512000, tzinfo=timezone.utc)


def test_vibration_pipeline_single_axis():
    pipeline = VibrationPipeline(sample_rate_hz=1000.0)
    t = np.linspace(0, 1.024, 1024, endpoint=False)
    samples = 1.0 * np.sin(2 * np.pi * 30.0 * t) + 0.1 * np.random.normal(0, 1, 1024)

    result = pipeline.process_window(samples, sample_rate_hz=1000.0)

    assert result.processing_version == "0.1"
    assert result.feature_version == "0.1"
    assert result.quality.valid is True
    assert result.quality.quality_score >= 0.90
    assert result.features.time_domain.rms > 0.5
    assert np.isclose(result.features.frequency_domain.dominant_frequency_hz, 30.0, atol=2.0)


def test_vibration_pipeline_multi_axis_vector_aggregation():
    pipeline = VibrationPipeline(sample_rate_hz=1000.0)
    generator = SyntheticVibrationGenerator(sample_rate_hz=1000.0, running_speed_hz=25.0)

    raw_channels = generator.generate_raw_window(scenario="imbalance", num_samples=1024)
    result = pipeline.process_window(raw_channels, sample_rate_hz=1000.0)

    assert result.quality.valid is True
    agg = result.features.aggregate
    assert "vector_rms" in agg
    assert "vector_peak" in agg
    assert "kurtosis" in agg
    assert "crest_factor" in agg
    assert "dominant_frequency_hz" in agg
    assert "spectral_energy" in agg

    # Imbalance has strong running speed component (25 Hz)
    assert np.isclose(agg["dominant_frequency_hz"], 25.0, atol=2.0)
    assert agg["vector_rms"] > 0.5


def test_pipeline_mechanical_impulse_behavior():
    pipeline = VibrationPipeline(sample_rate_hz=1000.0)
    generator = SyntheticVibrationGenerator(sample_rate_hz=1000.0, running_speed_hz=20.0)

    normal_window = generator.generate_raw_window(scenario="normal", num_samples=1024)
    impulse_window = generator.generate_raw_window(scenario="mechanical_impulse", num_samples=1024)

    normal_res = pipeline.process_window(normal_window)
    impulse_res = pipeline.process_window(impulse_window)

    # Impulse scenario must show elevated kurtosis and crest factor compared to normal
    assert impulse_res.features.aggregate["kurtosis"] > normal_res.features.aggregate["kurtosis"]
    assert impulse_res.features.aggregate["crest_factor"] > normal_res.features.aggregate["crest_factor"]


def test_pipeline_handles_corrupted_signal_cleanly():
    pipeline = VibrationPipeline(sample_rate_hz=1000.0)
    # Disconnected sensor (flatline)
    flatline = np.zeros(1024)
    result = pipeline.process_window(flatline)

    assert result.quality.valid is False
    assert "FLATLINE_SENSOR_DISCONNECTED" in result.quality.issues
    # Zeroed features to avoid corrupting analytics
    assert result.features.time_domain.rms == 0.0


def test_synthetic_acoustic_generator():
    ae_gen = SyntheticAcousticGenerator(sample_rate_hz=2000.0)
    samples = ae_gen.generate_raw_window(scenario="mechanical_impulse", num_samples=1024)

    assert len(samples) == 1024
    assert np.max(np.abs(samples)) > 0.5
