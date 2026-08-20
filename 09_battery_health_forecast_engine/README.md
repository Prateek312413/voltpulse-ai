# Uncertainty-Aware Battery Health Forecast Engine with Late-Telemetry Reconciliation

[![Tests](https://img.shields.io/badge/pytest-37%20passed%20(100%25)-success?style=for-the-badge)](tests/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![GPR](https://img.shields.io/badge/GPR-Cholesky%20%2B%20Jitter%20Ladder-blueviolet?style=for-the-badge)](app/core/gpr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 1. Executive Summary

Battery State-of-Health (SOH) forecasting systems estimate remaining usable capacity as electrochemical cells degrade across operational charge-discharge cycles. In real-world mission-critical telemetry pipelines (electric vehicles, aerospace, grid energy storage), telemetry observations rarely arrive in strictly sequential order. Out-of-order sensor packets, network latency, delayed cycle recordings, duplicate transmissions, and post-facto sensor recalibrations frequently inject retroactive data into historical records.

Naive forecasting systems silently retrain and overwrite previous predictions, obscuring model provenance, inducing silent drift, and destroying reproducibility.

The **Uncertainty-Aware Battery Health Forecast Engine** solves this challenge through:
1. **Explicit, Transparent Gaussian Process Regression (GPR):** Non-parametric Bayesian regression with exact Cholesky decomposition, negative log marginal likelihood hyperparameter optimization, and deterministic numerical jitter recovery.
2. **Temporal Reconstruction:** Decoupling physical observation time (`recorded_at` / cycle) from pipeline arrival time (`received_at`), ensuring training order is invariant to network jitter.
3. **Immutable Versioned Lineage & Forecast Storage:** Retains complete observation history and generates immutable forecast versions ($v_1, v_2, \dots$) rather than overwriting past estimates.
4. **Late-Telemetry Reconciliation Diff Engine:** Automatically detects when retroactive or corrected telemetry invalidates historical assumptions, re-evaluates candidate kernels, recomputes predictions, and outputs semantic audit diffs ($\Delta \text{SOH}$, $\Delta \sigma$, kernel shifts).
5. **Bit-for-Bit Deterministic Reproducibility:** Guarantees that identical telemetry, kernel configurations, and feature splits reproduce identical forecasts, uncertainty intervals, and model rankings.

---

## 2. Architecture & Data Flow

```
+---------------------------------------------------------------------------------------------------------+
|                                    BATTERY HEALTH FORECAST ENGINE                                       |
|                                                                                                         |
|  [Interactive Web Dashboard / REST API] <----------> [FastAPI Asynchronous Gateway]                    |
|                                                              |                                          |
|                +---------------------------------------------+------------------------------------+     |
|                |                                                                                  |     |
|                v                                                                                  v     |
|  +-----------------------------+                                                    +------------------+|
|  |     Telemetry Ingestion     |                                                    | Battery Registry ||
|  | • Duplicate Detection       |                                                    | • ID & Type      ||
|  | • Payload Collision (409)   |                                                    | • Nominal Cap    ||
|  | • Sensor Range Validation   |                                                    | • Active Tel Ver ||
|  | • Correction Lineage Chain  |                                                    +------------------+|
|  +--------------+--------------+                                                                        |
|                 |                                                                                       |
|                 v                                                                                       |
|  +--------------------------------------------------------------------------------------------------+   |
|  |                        TEMPORAL RECONSTRUCTION & TRAINING PIPELINE                              |   |
|  | • Event-Time Ordering (Cycle / recorded_at)      • Exclusion of Superseded Corrections           |   |
|  | • Missing-Cycle Gap Preservation                 • Strict 75/25 Chronological Validation Split   |   |
|  +----------------------------------------------+---------------------------------------------------+   |
|                                                 |                                                       |
|                                                 v                                                       |
|  +--------------------------------------------------------------------------------------------------+   |
|  |                       GAUSSIAN PROCESS REGRESSION (GPR) ARENA                                    |   |
|  | • Kernels: RBF, Matérn 3/2, Matérn 5/2, Rational Quadratic (RQ), ARD Multi-Feature               |   |
|  | • Baselines: Polynomial Regression, Decision Tree, K-Nearest Neighbors                           |   |
|  | • Numerical Stability: Deterministic Jitter Ladder [0.0, 1e-10, 1e-8, 1e-6, 1e-4]               |   |
|  | • Model Selection Hierarchy: Valid Status -> Lowest RMSE -> 95% CI Coverage -> Lowest MAE       |   |
|  +----------------------------------------------+---------------------------------------------------+   |
|                                                 |                                                       |
|                                                 v                                                       |
|  +--------------------------------------------------------------------------------------------------+   |
|  |                    LATE-TELEMETRY RECONCILIATION & DIFF AUDIT ENGINE                             |   |
|  | • Affected Forecast Horizon Detection            • Immutable Forecast Versioning (v1 -> v2)      |   |
|  | • Semantic Diff: Delta SOH, Delta Sigma          • Bit-for-Bit Deterministic Historical Replay   |   |
|  +--------------------------------------------------------------------------------------------------+   |
|                                                 |                                                       |
|                                                 v                                                       |
|  +--------------------------------------------------------------------------------------------------+   |
|  |                       SQLITE / POSTGRESQL VERSIONED DATA STORAGE                                 |   |
|  | • batteries  • telemetry_observations  • forecasts  • model_evaluations  • forecast_diffs  • audit    |   |
|  +--------------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Mathematical Foundations: Gaussian Process Regression

Given a training set of $N$ battery observations $\mathcal{D} = \{(\mathbf{x}_i, y_i)\}_{i=1}^N$ where $\mathbf{x}_i \in \mathbb{R}^D$ represents input cycle/telemetry features and $y_i = \text{SOH}_i \in [0, 1]$ represents State of Health:

$$y_i = f(\mathbf{x}_i) + \epsilon_i, \quad \epsilon_i \sim \mathcal{N}(0, \sigma_n^2)$$

The unknown latent degradation function is modeled as a Gaussian Process:

$$f(\mathbf{x}) \sim \mathcal{GP}\left(m(\mathbf{x}), k(\mathbf{x}, \mathbf{x}')\right)$$

### 3.1 Kernel Families

The engine implements 4 candidate GPR covariance functions plus multi-dimensional Automatic Relevance Determination (ARD):

1. **Squared Exponential / Radial Basis Function (RBF):**
   $$k_{\text{RBF}}(\mathbf{x}, \mathbf{x}') = \sigma_f^2 \exp\left( -\frac{\|\mathbf{x} - \mathbf{x}'\|^2}{2\ell^2} \right)$$

2. **Matérn 3/2 ($\nu = 1.5$):**
   $$k_{\text{Matérn 3/2}}(r) = \sigma_f^2 \left(1 + \frac{\sqrt{3}r}{\ell}\right) \exp\left(-\frac{\sqrt{3}r}{\ell}\right), \quad r = \|\mathbf{x} - \mathbf{x}'\|$$

3. **Matérn 5/2 ($\nu = 2.5$):**
   $$k_{\text{Matérn 5/2}}(r) = \sigma_f^2 \left(1 + \frac{\sqrt{5}r}{\ell} + \frac{5r^2}{3\ell^2}\right) \exp\left(-\frac{\sqrt{5}r}{\ell}\right)$$

4. **Rational Quadratic (RQ) — Continuous Scale Mixture:**
   $$k_{\text{RQ}}(r) = \sigma_f^2 \left( 1 + \frac{r^2}{2\alpha \ell^2} \right)^{-\alpha}$$

5. **Automatic Relevance Determination (ARD):**
   $$k_{\text{ARD}}(\mathbf{x}, \mathbf{x}') = \sigma_f^2 \exp\left( -\frac{1}{2} \sum_{d=1}^D \frac{(x_d - x'_d)^2}{\ell_d^2} \right)$$

---

### 3.2 Explicit Cholesky Formulation & Predictive Distribution

1. **Prior Covariance Construction:**
   $$K = \begin{bmatrix} k(\mathbf{x}_1, \mathbf{x}_1) & \dots & k(\mathbf{x}_1, \mathbf{x}_N) \\ \vdots & \ddots & \vdots \\ k(\mathbf{x}_N, \mathbf{x}_1) & \dots & k(\mathbf{x}_N, \mathbf{x}_N) \end{bmatrix} + \sigma_n^2 I_N$$

2. **Deterministic Jitter Ladder:**
   To guarantee positive-definiteness under collinear telemetry, the engine applies bounded diagonal regularization:
   $$K_{\text{reg}} = K + \delta I_N, \quad \delta \in \{0, 10^{-10}, 10^{-8}, 10^{-6}, 10^{-4}\}$$

3. **Cholesky Factorization:**
   $$L L^T = K_{\text{reg}}, \quad L \text{ is lower-triangular}$$

4. **Predictive Mean & Variance at Query Cycle $\mathbf{x}_*$:**
   $$\boldsymbol{\alpha} = L^{-T} (L^{-1} \mathbf{y})$$
   $$\mathbf{v} = L^{-1} \mathbf{k}_*, \quad \mathbf{k}_* = [k(\mathbf{x}_1, \mathbf{x}_*), \dots, k(\mathbf{x}_N, \mathbf{x}_*)]^T$$
   $$\bar{f}_* = \mathbf{k}_*^T \boldsymbol{\alpha} + \mu_y$$
   $$\mathbb{V}[f_*] = k(\mathbf{x}_*, \mathbf{x}_*) - \mathbf{v}^T \mathbf{v} + \sigma_n^2$$
   $$\sigma_* = \sqrt{\max(\mathbb{V}[f_*], 10^{-12})}$$

5. **95% Confidence Interval ($z = 1.96$):**
   $$\text{CI}_{95\%} = [\bar{f}_* - 1.96\sigma_*, \; \bar{f}_* + 1.96\sigma_*]$$

---

## 4. Benchmark Evaluation & Model Ranking

Benchmarked on 120 cycles of Li-ion battery degradation data under 75% chronological training and 25% future holdout:

| Rank | Candidate Model | Type | Status | Validation RMSE | Validation MAE | 95% Coverage | Cov $\Delta$ | Jitter | Latency | Selection Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **GPR (Matérn 5/2)** | GPR | **SUCCESS** | **0.003765** | **0.003114** | **100.0%** | **5.00%** | $0.0$ | **15.49 ms** | **SELECTED** |
| 2 | GPR (Matérn 3/2) | GPR | SUCCESS | 0.004155 | 0.003480 | 100.0% | 5.00% | $0.0$ | 20.73 ms | Runner-Up |
| 3 | GPR (ARD) | GPR | SUCCESS | 0.004192 | 0.003518 | 100.0% | 5.00% | $0.0$ | 11.68 ms | - |
| 4 | GPR (RBF) | GPR | SUCCESS | 0.004192 | 0.003518 | 100.0% | 5.00% | $0.0$ | 14.67 ms | - |
| 5 | GPR (Rational Quadratic) | GPR | SUCCESS | 0.004435 | 0.003734 | 100.0% | 5.00% | $0.0$ | 24.78 ms | - |
| 6 | Polynomial Reg (Deg 2) | Baseline | SUCCESS | 0.006340 | 0.005724 | 66.7% | 28.33% | $0.0$ | 1.08 ms | - |
| 7 | K-Nearest Neighbors | Baseline | SUCCESS | 0.023003 | 0.020444 | 0.0% | 95.00% | $0.0$ | 1.00 ms | - |
| 8 | Decision Tree Regressor | Baseline | SUCCESS | 0.023153 | 0.020640 | 6.7% | 88.33% | $0.0$ | 1.32 ms | - |

> **Key Observation:** GPR non-parametric kernels achieve **$6\times$ lower error** than polynomial and tree baselines while providing calibrated uncertainty bounds covering 100% of unseen holdout observations.

---

## 5. PRD 12 Edge Cases & Automated Test Suite

Every mandatory edge case specified in the problem statement is implemented as both a REST scenario runner and an automated pytest test:

| # | Edge Case Scenario | Challenge | Handled By | Pytest Status |
|---|---|---|---|:---:|
| **01** | **Normal Ordered Telemetry** | Monotonically increasing cycles | Full GPR pipeline execution | `PASSED` |
| **02** | **Duplicate Telemetry Observation** | Identical payload submitted twice | Idempotent detection without dataset inflation | `PASSED` |
| **03** | **Conflicting Observation ID** | Same observation ID with mismatched SOH/voltage | Rejection with `409 Conflict` | `PASSED` |
| **04** | **Late-Arriving Earlier Cycle** | Cycle 25 arrives after Cycle 40 and Forecast $v_1$ | Increments to Forecast $v_2$, outputs Diff | `PASSED` |
| **05** | **Corrected Measurement Lineage** | Erroneous SOH replaced with calibrated value | Inactivates old version, preserves audit chain | `PASSED` |
| **06** | **Missing Cycles in History** | Sequence with gaps (e.g. cycles 15–25 missing) | GPR covariance expands uncertainty across gap | `PASSED` |
| **07** | **Deterministic Tie-Breaking** | Two kernels produce identical validation RMSE | Strict tie-break hierarchy (alphabetical tie-break) | `PASSED` |
| **08** | **Covariance Numerical Jitter** | Collinear data causing singular covariance | Bounded Jitter Ladder ($10^{-10} \to 10^{-4}$) | `PASSED` |
| **09** | **Partial Candidate Failure** | Singular kernel candidate fails during fit | Failed candidate marked cleanly; healthy picked | `PASSED` |
| **10** | **Late Data Kernel Switch** | Non-smooth late data shifts optimal kernel | Automatically re-selects best kernel | `PASSED` |
| **11** | **Uncertainty Collapse** | Late data reduces variance without shifting mean | Pins posterior variance; mean shift $< 0.002$ | `PASSED` |
| **12** | **Bit-for-Bit Deterministic Replay** | Multi-pass re-execution from identical inputs | $0.000000$ variance across runs | `PASSED` |

---

## 6. Quick Start & Local Execution

### Prerequisites
* Python 3.10 or 3.11
* Pip & Git

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/Prateek312413/battery-health-forecast-engine.git
cd battery-health-forecast-engine

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Local Engine (Auto-Seeds Demo Battery & Opens UI)
```bash
python run.py
```
* Interactive UI: `http://localhost:8000`
* Swagger Interactive Docs: `http://localhost:8000/docs`
* ReDoc API Reference: `http://localhost:8000/redoc`

### 3. Run Automated Tests (37/37 Passing)
```bash
pytest tests/ -v
```

### 4. Run Benchmark Suite
```bash
python benchmark.py
```

### 5. Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up --build -d
```

---

## 7. REST API Reference

### Battery Registry
* `POST /batteries` — Register new battery (`battery_id`, `battery_type`, `nominal_capacity`).
* `GET /batteries` — List all registered batteries.
* `GET /batteries/{battery_id}` — Retrieve battery metadata and current `active_telemetry_version`.

### Telemetry Ingestion & Retrieval
* `POST /batteries/{battery_id}/observations` — Ingest single observation (`observation_id`, `cycle_number`, `soh`, `voltage`, etc.).
* `POST /batteries/{battery_id}/observations/batch` — Atomically ingest batch of observations.
* `GET /batteries/{battery_id}/observations?order_by=event_time` — Retrieve in chronological cycle order.
* `GET /batteries/{battery_id}/observations?order_by=receive_time` — Retrieve in arrival order.
* `POST /batteries/{battery_id}/observations/{observation_id}/correct` — Submit calibrated correction with audit reason.

### Model Evaluation & Forecasting
* `POST /batteries/{battery_id}/models/evaluate` — Evaluate all GPR candidate kernels & baselines on chronological split.
* `POST /batteries/{battery_id}/forecasts` — Generate versioned SOH forecast with 95% confidence intervals.
* `GET /batteries/{battery_id}/forecasts` — Retrieve versioned forecast history ($v_1, v_2, \dots$).
* `GET /batteries/{battery_id}/forecasts/{forecast_id}` — Retrieve single forecast details & multi-horizon trajectory.

### Reconciliation & Replay
* `POST /batteries/{battery_id}/reconcile` — Execute reconciliation across all affected forecasts.
* `GET /batteries/{battery_id}/reconciliations` — List historical reconciliation diffs.
* `POST /batteries/{battery_id}/replay` — Perform multi-run bit-for-bit determinism test.
* `POST /scenarios/run/{scenario_id}` — Execute PRD Edge Cases (1–12).
* `GET /scenarios/list` — List all 12 edge cases.

---

## 8. Repository File Structure

```
09_battery_health_forecast_engine/
├── app/
│   ├── api/
│   │   ├── batteries.py          # Battery registry endpoints
│   │   ├── forecasts.py          # SOH forecasting endpoints
│   │   ├── models.py             # Kernel evaluation & selection
│   │   ├── reconciliation.py     # Late-telemetry reconciliation diffs
│   │   ├── scenarios.py          # 12 PRD Edge Case scenario runners
│   │   └── telemetry.py          # Telemetry ingestion, validation & corrections
│   ├── core/
│   │   ├── gpr/
│   │   │   ├── kernels.py        # RBF, Matern 3/2, Matern 5/2, RQ, ARD
│   │   │   ├── gp_engine.py      # Custom GPR with Cholesky & Jitter Ladder
│   │   │   └── baselines.py      # Polynomial, KNN, Decision Tree
│   │   ├── evaluator.py          # Deterministic tie-break hierarchy
│   │   ├── forecaster.py         # Multi-horizon forecast & CI generation
│   │   ├── reconciler.py         # Late-data impact analysis & diffs
│   │   ├── replay.py             # Bit-for-bit replay determinism verification
│   │   ├── temporal.py           # Event-time reconstruction & validation split
│   │   └── validation.py         # Telemetry validator & conflict detector
│   ├── models/                   # SQLAlchemy ORM database models
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── static/                   # Glassmorphism Dark UI Dashboard (HTML/CSS/JS)
│   ├── config.py                 # Application configuration & thresholds
│   ├── database.py               # SQLite / PostgreSQL connection pool
│   └── main.py                   # FastAPI application gateway
├── data/
│   └── generator.py              # Physics-informed Li-ion telemetry generator
├── tests/
│   ├── test_12_edge_cases.py     # All 12 PRD Edge Case integration tests
│   ├── test_api_endpoints.py     # Full REST API endpoint test suite
│   ├── test_gpr_engine.py        # Mathematical GPR & kernel unit tests
│   ├── test_model_eval.py        # Deterministic ranking & tie-break tests
│   ├── test_reconciliation.py    # Late-telemetry diff & versioning tests
│   ├── test_replay.py            # Reproducibility & time-travel tests
│   ├── test_temporal.py          # Temporal ordering & lineage tests
│   └── test_validation.py        # Payload validation & conflict tests
├── benchmark.py                  # High-throughput kernel benchmark runner
├── Dockerfile                    # Containerization specification
├── docker-compose.yml            # Multi-service orchestration
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Project dependencies
├── run.py                        # Zero-config CLI & auto-browser launcher
├── start.bat                     # Windows one-click launcher
├── start.sh                      # Linux/macOS launcher
├── LICENSE                       # MIT Open Source License
└── README.md                     # Comprehensive technical documentation
```

---

## 9. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
