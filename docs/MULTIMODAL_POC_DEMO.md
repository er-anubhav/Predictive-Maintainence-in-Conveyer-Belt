# SIH 26008 — Multimodal POC Judge Demonstration Guide

**Target Presentation Time**: 3–5 Minutes  
**Demonstration Scope**: Live Multimodal Conveyor Condition Monitoring with Explainable Evidence Fusion.  

---

## 1. Step-by-Step Judge Flow

### Step 1: Baseline Normal (30 Seconds)
1. In the top-right **Demo Control** dropdown, ensure **Normal Operation** is selected.
2. Show the **OVERALL CONVEYOR CONDITION**:
   - Status: `NORMAL` (Emerald badge)
   - Explainable WHY: *"Monitored modalities are within their configured POC baseline ranges."*
3. Highlight the **Optical Camera Feed**:
   - Point out the centered belt edges and clean texture.
   - Point out the clear `DEMO / SIMULATED` watermark.
4. Show the **ML Engine Card**:
   - Model: `IF-v0.3.1 (Frozen)`
   - Commissioning: `v0.5 Local Run-In Envelope`
   - Decision Layer: `v0.6.1 Dual Persistence`

---

### Step 2: Trigger Belt Misalignment (45 Seconds)
1. Select **Belt Misalignment** from the Demo Control dropdown.
2. Observe immediate updates without page refresh:
   - Tracking meter jumps to $+16.5 \text{ mm}$ (`Drift Alert`).
   - Camera visual status transitions to `WARNING` (shows $+42\text{px}$ belt edge displacement).
   - **Overall Conveyor Condition**: Updates to `WARNING`.
   - **Explainable WHY**:
     * *"Tracking deviation co-occurs with abnormal vibration during the current operating state."*
3. **Key Judge Talking Point**:
   > *"Notice how the system doesn't guess a random failure probability. It directly correlates the lateral laser sensor drift with the optical camera edge displacement."*

---

### Step 3: Trigger Bearing Anomaly (45 Seconds)
1. Select **Bearing Anomaly**.
2. Point to the **Vibration Anomaly Detection** card:
   - Anomaly score jumps to $> 0.85$.
   - Composite deviation increases to $> 4.0\sigma$.
   - Dual-persistence activates (3-of-5 and 5-of-9 window confirmation).
3. Point to the Multimodal Card:
   - Condition: `WARNING` $\rightarrow$ `HIGH_SEVERITY` as persistence accumulates.
   - Reason explains: *"Persistent vibration anomaly detected by the frozen vibration monitoring pipeline."*

---

### Step 4: Trigger Thermal Event (45 Seconds)
1. Select **Thermal Event**.
2. Temperature jumps to $82.5^\circ\text{C}$ with elevated rate of rise.
3. Observe compound evidence fusion:
   - Condition: `HIGH_SEVERITY`
   - Reason: *"Rapid temperature rise co-occurs with elevated vibration."*
4. **Key Judge Talking Point**:
   > *"A single thermal transient could be ambient noise, but when correlated with mechanical vibration, the fusion engine identifies severe compound bearing friction."*

---

### Step 5: Trigger Visible Belt Damage (45 Seconds)
1. Select **Visible Belt Damage**.
2. Point directly to the **Camera Inspection Feed**:
   - Camera analyzes localized surface anomaly (score $1.00$).
   - Frame shows surface rip / splice tear artifact highlighted in the ROI.
   - Overall Condition: `HIGH_SEVERITY`.
   - Reason: *"Persistent vibration anomaly co-occurs with visual belt-surface abnormality."*

---

### Step 6: Trigger Compound Multimodal Event & Reset (30 Seconds)
1. Select **Multimodal Event**:
   - Simultaneous Vibration + Thermal ($85^\circ\text{C}$) + Tracking ($+18.5\text{ mm}$) + Camera Damage.
   - Condition: `HIGH_SEVERITY`.
   - System lists all corroborating modalities in the WHY section.
2. Click **RESET**:
   - System returns cleanly to `NORMAL` operation.

---

## 2. Integrity Points to Highlight to Judges

1. **Frozen ML Engine**: Base vibration model is strictly frozen (`IF-v0.3.1`, SHA-256 verified) with zero test-set contamination.
2. **Transparent Explainability**: No black-box neural fusion. Explicit deterministic engineering rules tell the operator exactly *which* sensor saw *what*.
3. **Decoupled Optical Pipeline**: Camera image capture is completely asynchronous from telemetry ingestion.
4. **No Direct Image Blobs in Database**: Clean reference-based storage (`data/evidence/camera/`) keeps database lean.
5. **Heuristic Severity**: We do not claim an uncertified "99.8% probability of failure". We report calibrated, observable evidence.
