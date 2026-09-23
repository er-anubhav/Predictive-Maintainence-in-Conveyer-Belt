# Signal Processing & Feature Extraction Foundation — SIH 26008

## Intelligent Conveyor Belt Health & Predictive Maintenance in Iron Ore Mining

---

## 1. Architectural Motivation & Bandwidth Trade-Offs

In heavy industrial environments such as remote iron ore mining sites, continuous streaming of uncompressed, high-frequency raw time series from distributed edge sensor nodes directly to central cloud servers is architecturally unviable:

1. **Cellular / Low-Power Wireless Bottlenecks**:
   A single tri-axial accelerometer sampling at $1000\text{ Hz}$ with double-precision floating point generates:
   $$\text{Bandwidth per node} = 3 \text{ channels} \times 1000 \frac{\text{samples}}{\text{sec}} \times 8 \frac{\text{bytes}}{\text{sample}} = 24\text{ KB/sec} \approx 2.07\text{ GB/day/node}$$
   Across an overland conveyor belt system with 50 sensor nodes, continuous streaming would demand $> 100\text{ GB/day}$ of constant uplink bandwidth with high packet-loss risk during rain or pit cellular dead-zones.
2. **Computational Offloading to the Edge**:
   By processing raw signal windows locally at the edge (either directly on node microcontrollers or local Edge Gateways), the raw array of $1024$ samples ($\approx 24\text{ KB}$) is reduced to a concise canonical telemetry frame of $\approx 350\text{ bytes}$ transmitted every $1 - 2\text{ seconds}$ ($\sim 0.2\text{ KB/sec}$), representing a **$> 98\%$ bandwidth reduction**.
3. **Deterministic Foundation for Machine Learning**:
   Raw accelerometer signals contain high levels of stochastic environmental noise (ore dumping impact, motor electromagnetic interference). Signal processing converts noisy time series into stationary, mathematically interpretable physical features (RMS, kurtosis, crest factor, dominant frequency, spectral energy). These features serve as the clean input vectors for future anomaly detection and remaining useful life (RUL) predictive models.

---

## 2. Sampling Standards & Windowing Strategy

### 2.1 Sensor Sampling Frequencies

- **Vibration Channels ($X, Y, Z$)**: $f_s = 1000\text{ Hz}$ ($\Delta t = 1.0\text{ ms}$).
  - *Nyquist Frequency*: $f_{\text{Nyquist}} = \frac{f_s}{2} = 500\text{ Hz}$.
  - *Coverage*: Captures conveyor drive pulley rotational fundamental ($\approx 20\text{ Hz}$ for a 1200 RPM drive) up to the 25th harmonic, idler roll passing frequencies, and bearing defect frequencies (BPFO, BPFI).
- **Acoustic Emission Channel ($AE$)**: $f_s = 2000\text{ Hz}$ envelope sampling.
  - Captures high-frequency acoustic burst envelopes from metal-on-metal friction, belt edge skirt rubbing, and bearing cage degradation.

### 2.2 Windowing & Segmentation

- **Window Size ($N$)**: $1024$ samples ($\approx 1.024\text{ seconds}$ duration at $1000\text{ Hz}$).
  - Powers of 2 ($N = 2^{10}$) maximize Fast Fourier Transform (FFT) computational efficiency.
  - Spectral resolution: $\Delta f = \frac{f_s}{N} = \frac{1000}{1024} \approx 0.9765\text{ Hz/bin}$.
- **Overlap**: $50\%$ sliding overlap ($512$ sample step).
  - Ensures transient shock impulses occurring near window edges are captured with full amplitude in adjacent windows.
- **Tapering Windows**:
  - Rectangular (for uniform statistical time moments).
  - Hann and Hamming windows ($w[n] = 0.54 - 0.46 \cos\frac{2\pi n}{N}$) applied prior to FFT to suppress spectral leakage side-lobes.

---

## 3. Preprocessing & Filtering Pipeline

Before feature extraction, raw signals undergo three stages of signal conditioning:

```
Raw Channel Time Series x[n]
           ↓
   1. DC Removal: x_zero[n] = x[n] - mean(x)
           ↓
   2. Linear Detrending: x_detrend[n] = x_zero[n] - (α*t + β)
           ↓
   3. Zero-Phase Butterworth Filter: sosfiltfilt(SOS, x_detrend)
           ↓
   Conditioned Clean Signal y[n]
```

### 3.1 DC Bias Removal & Detrending
- Eliminates sensor zero-offset calibration drift and sensor mounting tilt (gravity component $1\text{g}$ projection onto accelerometer axes).
- Linear regression detrending eliminates thermal slope drift during startup and prolonged operation.

### 3.2 Second-Order Sections (SOS) Butterworth Filtering
- **Filter Order**: 4th-order Butterworth ($24\text{ dB/octave}$ roll-off).
- **Passband**: $2.0\text{ Hz} \dots 450.0\text{ Hz}$ (Bandpass).
  - Low cutoff ($2.0\text{ Hz}$) rejects low-frequency structural sway and building vibrations.
  - High cutoff ($450.0\text{ Hz}$) acts as a strict anti-aliasing guard well below Nyquist ($500.0\text{ Hz}$).
- **Zero-Phase Filtering (`sosfiltfilt`)**:
  - Forward-backward filtering yields **zero phase distortion** ($\phi(f) \equiv 0$), preserving exact temporal alignment of impact peaks and wave packet arrivals.
  - Second-Order Sections (SOS) prevent numerical instability and pole-zero quantization errors encountered with traditional transfer functions.

---

## 4. Engineering Feature Extraction

From each conditioned window $y[n]$ ($n = 0 \dots N-1$), the pipeline extracts standard mechanical and statistical features:

### 4.1 Time-Domain Metrics

| Metric | Formula | Normal Baseline | Physical Diagnostic Significance |
|---|---|---|---|
| **Mean** ($\mu$) | $\frac{1}{N}\sum y_i$ | $\approx 0.0$ | Zero baseline check. |
| **RMS** ($x_{\text{rms}}$) | $\sqrt{\frac{1}{N}\sum y_i^2}$ | $0.20 \dots 0.50\text{ g}$ | Overall kinetic vibration energy. Direct indicator of general operational severity (ISO 10816). |
| **Peak** ($x_{\text{peak}}$) | $\max |y_i|$ | $0.80 \dots 1.50\text{ g}$ | Maximum instantaneous acceleration. |
| **Peak-to-Peak** ($x_{\text{p2p}}$) | $\max(y_i) - \min(y_i)$ | $1.50 \dots 3.00\text{ g}$ | Total dynamic displacement range. |
| **Crest Factor** ($C_f$) | $\frac{x_{\text{peak}}}{x_{\text{rms}}}$ | $1.30 \dots 1.80$ (Sine $\approx 1.414$) | Ratio of peak shock to continuous energy. Elevates early ($> 3.5$) during bearing spalling, crack formation, or belt splice slap before RMS increases. |
| **Variance** ($\sigma^2$) | $\frac{1}{N}\sum (y_i - \mu)^2$ | Dependent on load | AC signal power. |
| **Skewness** ($S$) | $\frac{\frac{1}{N}\sum(y_i - \mu)^3}{\sigma^3}$ | $\approx 0.0$ | Asymmetry of vibration waveform. Non-zero skewness indicates directional binding or one-sided roller rubbing. |
| **Kurtosis** ($\beta_2$) | $\frac{\frac{1}{N}\sum(y_i - \mu)^4}{\sigma^4}$ | Gaussian $\approx 3.0$ | Sensitivity to sharp transient impact shocks. Normal background vibration is Gaussian ($\sim 3.0$); bearing defect impact pulses drive $\beta_2 > 5.0 - 15.0$. |

### 4.2 Frequency-Domain Metrics (Real FFT)

Computed via Real Fast Fourier Transform ($X[k] = \text{rfft}(y[n] \cdot w[n])$) across $K = N/2 + 1 = 513$ frequency bins:

| Metric | Formula / Method | Engineering Utility |
|---|---|---|
| **Dominant Frequency** ($f_0$) | $\arg\max_{f_k > 0} |X[k]|$ | Identifies primary driving rotational harmonic (shaft speed, pulley rotation $\approx 20\text{ Hz}$). |
| **Spectral Energy** ($E_{\text{spec}}$) | $\frac{1}{N}\sum_{k=0}^{K-1} |X[k]|^2$ | Total frequency-domain power density. Conserves time-domain variance by Parseval's theorem. |
| **Spectral Centroid** ($f_c$) | $\frac{\sum f_k |X[k]|}{\sum |X[k]|}$ | Center of spectral mass. Shifts upward toward higher frequencies as surface friction and bearing roughness escalate. |
| **Spectral Bandwidth** ($\sigma_f$) | $\sqrt{\frac{\sum (f_k - f_c)^2 |X[k]|}{\sum |X[k]|}}$ | Frequency dispersion around centroid. Narrow in pure unbalance; wide in turbulent bearing degradation. |
| **Spectral Entropy** ($H_{\text{spec}}$) | $-\sum p_k \log_2(p_k) / \log_2(K)$ | Measure of spectral complexity. Low ($< 0.4$) for harmonic tones; high ($> 0.8$) for white noise and structural chaotic vibrations. |

### 4.3 Mechanical Band Energy Partitioning

Frequency bins are grouped into diagnostic sub-bands:
1. **Sub-Synchronous ($0 \dots 10\text{ Hz}$)**: Belt sagging, frame structural oscillation, low-frequency conveyor surge.
2. **$1\times$ Running Speed ($10 \dots 30\text{ Hz}$)**: Motor drive pulley unbalance ($f_0 \approx 20\text{ Hz}$ at 1200 RPM).
3. **Harmonics ($30 \dots 100\text{ Hz}$)**: $2\times$ and $3\times$ alignment harmonics, shaft coupling misalignment, idler roll passing.
4. **High Frequency ($100 \dots 500\text{ Hz}$)**: Bearing race defect frequencies (BPFO, BPFI), idler bearing pitting, metal-on-metal impact ringing.

---

## 5. Multi-Axis Vector Aggregation

To produce a single set of standardized telemetry metrics without losing directional severity, the 3 synchronized channels ($X, Y, Z$) are aggregated into vector metrics:

- **Vector RMS**:
  $$\text{Vector RMS} = \sqrt{\text{RMS}_x^2 + \text{RMS}_y^2 + \text{RMS}_z^2}$$
- **Vector Peak**:
  $$\text{Vector Peak} = \max(\text{Peak}_x, \text{Peak}_y, \text{Peak}_z)$$
- **Aggregate Crest Factor**:
  $$\text{Aggregate } C_f = \frac{\text{Vector Peak}}{\text{Vector RMS}}$$
- **Dominant Shock Kurtosis**:
  $$\text{Aggregate Kurtosis} = \max(\text{Kurt}_x, \text{Kurt}_y, \text{Kurt}_z)$$
- **Dominant Axis Identification**:
  The pipeline evaluates spectral energy on $X$, $Y$, and $Z$; the channel exhibiting the highest energy is selected as the dominant axis for reporting $f_0$.

---

## 6. Signal Quality & Sensor Health Auditing

Before extracting features, raw input buffers pass through the `SignalQualityAuditor` to protect downstream analytics against invalid data:

1. **Empty / Null Buffers**: Signals with zero length or non-array inputs are immediately flagged.
2. **Non-Finite Detection**: Detects `NaN` or `±Inf` values caused by ADC serial transmission corruption.
3. **Flatline / Disconnected Sensor Detection**:
   $$\sigma = \text{std}(x) < 10^{-6}$$
   A signal with zero variance indicates a disconnected cable, broken transducer, or frozen ADC.
4. **Rail Saturation / Clipping**:
   Detects if $> 1.0\%$ of samples reside at the positive or negative sensor measurement rails ($\pm 16\text{g}$).
5. **Sample Rate Validity**: Verifies $f_s > 0$ and window sample count $N \ge 32$.
6. **Quality Score**: Produces a normalized score ($0.0 \dots 1.0$) and human-readable diagnostic issue tags (`["FLATLINE_DETECTED", "RAIL_CLIPPING"]`).

---

## 7. Performance Benchmarks

Latency and memory footprint measured across 100 iterations on standard CPU hardware (`ml/benchmark.py`):

| Window Size ($N$) | Time Span ($f_s=1000\text{ Hz}$) | Mean Latency | Peak Latency | Peak Memory Overhead | Real-Time Overhead Margin |
|---|---|---|---|---|---|
| **1024 samples** | $1.024\text{ s}$ | **$23.8\text{ ms}$** | $31.2\text{ ms}$ | **$331\text{ KB}$** | **$43\times$ faster than real-time** |
| **2048 samples** | $2.048\text{ s}$ | **$24.1\text{ ms}$** | $29.8\text{ ms}$ | **$145\text{ KB}$** | **$85\times$ faster than real-time** |
| **4096 samples** | $4.096\text{ s}$ | **$30.4\text{ ms}$** | $40.5\text{ ms}$ | **$256\text{ KB}$** | **$135\times$ faster than real-time** |

With a complete multi-axis window processing cycle executing in $< 25\text{ ms}$, edge processors comfortably run the full feature extraction pipeline while maintaining $> 95\%$ CPU idle time for network stack and buffer operations.

---

## 8. Architectural Boundary & Relationship to Future ML

> [!IMPORTANT]
> **Strict Separation of Concerns**:
> - **Milestone 3 Responsibility**: Deterministic signal conditioning, digital filtering, Fast Fourier Transforms, statistical moment computation, and signal quality auditing.
> - **Out of Scope for Milestone 3**: Machine learning classifiers, Isolation Forests, Autoencoders, One-Class SVMs, health scores ($0-100\%$), failure probability calculations, or Remaining Useful Life (RUL) estimates.
>
> The verified engineering features produced in this milestone (`vibration_rms`, `vibration_peak`, `vibration_kurtosis`, `crest_factor`, `dominant_frequency_hz`, `spectral_energy`) form the official feature vector representation required to train and evaluate future predictive ML models in subsequent milestones.
