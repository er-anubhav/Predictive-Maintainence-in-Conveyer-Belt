# Machine Learning & Predictive Analytics Module

## Future Purpose
The `ml/` module will contain analytical models, predictive maintenance pipelines, and anomaly detection algorithms for conveyor belt and joint degradation in iron ore mining.

In future phases, this module will implement:
- **Multimodal Sensor Fusion**: Joint analysis of vibration spectra, acoustic signatures, belt speed, and temperature.
- **Unsupervised Anomaly Detection**: Autoencoders and Isolation Forests trained on baseline normal operational regimes to identify early-stage belt splice tearing and roller bearing wear.
- **Remaining Useful Life (RUL) Estimation**: Time-to-failure regression models and degradation trend forecasting.
- **Edge Model Optimization**: Quantized TFLite/ONNX models exported for on-device inference on gateway hardware.

*Note: In Milestone 1, no ML models or anomaly scores are evaluated. Only telemetry storage and dashboarding are provided.*
