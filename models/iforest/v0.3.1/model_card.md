# Isolation Forest v0.3.1 Model Card (LEAKAGE-CORRECTED RESEARCH MODEL)

## 1. Model Overview & Purpose
- **Architecture**: `sklearn.ensemble.IsolationForest` (`n_estimators=200`, `contamination=0.03`, `random_state=42`)
- **Version**: `v0.3.1` (LEAKAGE-CORRECTED RESEARCH MODEL)
- **Objective**: Rigorous validation-only selection and multi-domain real-normal representation learning.
- **Production Status**: **RESEARCH PROTOTYPE ONLY — NOT FOR PRODUCTION DEPLOYMENT**.

## 2. Leakage-Free Development Protocol
- **Partitioning**: Strictly whole-recording disjoint partition (`metadata/v0.3.1_split_manifest.json`).
- **Feature Selection**: Validation-only comparison between Standard 6 and Scale-Robust features.
- **Winning Strategy**: `Strategy_A_Standard6` (`rms, peak, crest_factor, kurtosis, dominant_frequency_hz, spectral_energy`).
- **Supervised Threshold Calibration**: Calibrated on validation partition to maximize F1 under FPR <= 0.10 constraint. Frozen at 0.590.
- **Test Set Firewall**: Sealed prior to model freeze and opened exactly once.

## 3. Disaggregated Test Results (Evaluated Post-Freeze)

### CWRU Held-Out Test Partition (`100.mat`, `108.mat`, `130.mat`):
- **Precision**: 0.4606
- **Recall**: 0.6667
- **F1 Score**: 0.5448
- **Healthy FPR**: 0.3911
- **Confusion Matrix**: TP=158, FP=185, TN=288, FN=79

### Paderborn Held-Out Test Partition (15 K001 runs, 70 KA01 runs, 70 KA04 runs):
- **Precision**: 0.9907
- **Recall**: 0.5631
- **F1 Score**: 0.7180
- **Healthy FPR**: 0.0493
- **Confusion Matrix**: TP=19654, FP=184, TN=3551, FN=15251

## 4. Key Limitations & Disclaimers
1. **Recording-Level Generalization Only**: Because Paderborn K001 recordings stem from the same physical bearing specimen under varied conditions, this model demonstrates *recording-level cross-condition generalization*, not *independent-bearing generalization*.
2. **Conveyor Invalidation**: Public motor test-rig benchmarks do not model conveyor idler transients, ore loading spikes, or belt sag.
