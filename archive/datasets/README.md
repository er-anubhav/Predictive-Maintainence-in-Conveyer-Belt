# Development Datasets & Offline Recording Facility

This directory stores raw high-frequency sensor time-series recordings and processed feature matrices for offline algorithm validation and future ML model training.

## Directory Structure

```
datasets/
├── raw/
│   ├── vibration/        # Raw 3-axis accelerometer time-series (.npz)
│   └── acoustic/         # Raw acoustic emission time-series (.npz)
├── processed/
│   └── features/         # Extracted feature tabular records (.npz / .parquet)
├── recorder.py           # Python utility for saving and loading sample recordings
└── README.md
```

## Metadata Schema

Every `.npz` recording includes embedded metadata:
- `node_id`: Edge hardware identifier (e.g. `NODE-001`)
- `conveyor_id`: Conveyor asset identifier (e.g. `Conveyor-01`)
- `sensor`: Modality (`vibration` or `acoustic`)
- `scenario`: Simulated fault condition (`normal`, `misalignment`, `imbalance`, `mechanical_impulse`, `noisy_sensor`)
- `timestamp`: UTC ISO timestamp
- `sample_rate_hz`: Sampling frequency (e.g. 1000 Hz)
- `duration_seconds`: Total duration of recording
- `processing_version`: Processing pipeline version tag (e.g. `0.1`)

## Usage Example

```python
from datasets.recorder import record_raw_dataset, load_raw_dataset
from ml.simulator.vibration import SyntheticVibrationGenerator

generator = SyntheticVibrationGenerator(sample_rate_hz=1000)
raw_window = generator.generate_raw_window(scenario="mechanical_impulse", num_samples=2048)

file_path = record_raw_dataset(
    node_id="NODE-001",
    conveyor_id="Conveyor-01",
    sensor="vibration",
    scenario="mechanical_impulse",
    samples=raw_window,
    sample_rate_hz=1000,
)
print(f"Saved recording to: {file_path}")
```
