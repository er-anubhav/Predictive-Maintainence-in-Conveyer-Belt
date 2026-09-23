# Isolation Forest v0.5 Model Card (MACHINE-AGNOSTIC COMMISSIONING RESEARCH MODEL)

## 1. Model Overview & Purpose
- **Architecture**: `sklearn.ensemble.IsolationForest` (`n_estimators=200`, `contamination=0.03`, `random_state=42`)
- **Version**: `v0.5`
- **Scientific Role**: **MACHINE-AGNOSTIC COMMISSIONING RESEARCH MODEL**
- **Production Status**: **NOT PRODUCTION VALIDATED — QUARANTINED EXPERIMENTAL PROTOTYPE**.
- **Objective**: Deployment-style commissioning mechanism in which a new edge sensor establishes its local healthy operating envelope from a verified healthy run-in period with zero domain or machine metadata.

## 2. Operational Separation of Modes
> **Explicit Notice**:
> IF-v0.5 evaluates a deployment-style commissioning mechanism in which a new edge sensor establishes its local healthy operating envelope from a verified healthy run-in period. Healthy commissioning stability is evaluated independently from fault sensitivity.

- **Mode A (Healthy Commissioning Stability)**: Evaluated on unseen healthy recordings (`100.mat` + 15 K001 runs).
- **Mode B (Fault Sensitivity)**: Formally documented as `NOT ESTABLISHABLE FROM CURRENT PADERBORN PROTOCOL` due to lack of pre-damage healthy baselines in Paderborn KA01/KA04.

## 3. Mode A Test Results (Healthy Commissioning Stability)
- **CWRU Normal (`100.mat`)**: 0 Persistent Alarms (Avg Persistent FPR = **0.00%**).
- **Paderborn Healthy (`K001` 15 runs)**: 0 Persistent Alarms (Avg Persistent FPR = **0.00%**).
- **Temporal Persistence Policy**: 3-of-5 consecutive windows.

## 4. Operational Boundaries & Disclaimer
This model is not validated for mining conveyor systems. Conveyor idlers undergo dynamic bulk-material loading spikes that require empirical run-in baseline characterization on running conveyors.
