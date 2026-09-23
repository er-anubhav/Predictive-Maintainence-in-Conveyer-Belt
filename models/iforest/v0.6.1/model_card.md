# IF-v0.6.1 Model Card: Evidence & Persistence Layer
**Version**: IF-v0.6.1
**Date**: 2026-09-22
**Status**: EVIDENCE PIPELINE CORRECTION — NOT PRODUCTION VALIDATED

---

## 1. Model Summary
- **Base Anomaly Representation**: Frozen `IF-v0.3.1` Isolation Forest (`n_estimators=200`, `contamination=0.03`, `random_state=42`) trained on CWRU Standard 6 features.
- **Commissioning Protocol**: Machine-agnostic 20% healthy run-in interval (`v0.5`).
- **Temporal Decision Logic**: Dual-rate persistence filter (**3-of-5** for Warning / Maintenance Alert Candidate, **5-of-9** for High-Severity Alert Candidate).
- **Evidence Extraction**: Robust per-feature Z-deviations and quality checks. Arbitrary confidence figures eliminated (`confidence: null`).

---

## 2. Dynamic Performance Verification Summary
- **Paderborn K001 False Alarm Rate**:
  - Instantaneous ($z \ge 3.0$): **32.96%** (5277 windows)
  - 3-of-5 Persistence: **24.09%** (3856 windows)
  - 5-of-9 Persistence: **20.33%** (3254 windows)
- **NASA IMS Commissioning Interval**:
  - Instantaneous Spurious Alarms: 54
  - 3-of-5 Alarms: **0**
  - 5-of-9 Alarms: **0**
- **NASA Degradation Trajectory**:
  - Persistent 3-of-5 Onset: **Snapshot #196** (19.9% run life)
  - Persistent 5-of-9 Onset: **Snapshot #222** (22.6% run life)
  - Detection Buffer Delay: **26 snapshots (260 minutes)**
