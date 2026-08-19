"""
Unit tests for Gaussian Process Regression Forecaster, Multi-Kernel Evaluation, and Bayesian Uncertainty.
"""

import pytest
import numpy as np
from voltpulse.core.gpr_forecaster import (
    GaussianProcessForecaster,
    GPRKernelType,
)


def test_gpr_forecaster_multi_kernel_evaluation():
    forecaster = GaussianProcessForecaster()
    cycles = [float(i * 10) for i in range(1, 25)]
    # SOH declining from 100% down to 92%
    sohs = [100.0 - 0.035 * c + np.random.normal(0, 0.05) for c in cycles]

    evaluations = forecaster.evaluate_candidate_kernels(cycles, sohs)
    assert len(evaluations) == 5
    # Best rank is 1
    assert evaluations[0].rank == 1
    assert evaluations[0].rmse < 2.0
    assert evaluations[0].coverage_95_pct > 60.0


def test_gpr_forecast_uncertainty_envelopes():
    forecaster = GaussianProcessForecaster()
    cycles = [float(i * 15) for i in range(1, 20)]
    sohs = [100.0 - 0.04 * c for c in cycles]

    res = forecaster.forecast(
        battery_id="TEST-BESS-01",
        cycles=cycles,
        sohs=sohs,
        forecast_horizon_cycles=120
    )

    assert res.battery_id == "TEST-BESS-01"
    assert len(res.forecast_curve) > 0

    # Test uncertainty expands into the future (epistemic uncertainty increases)
    first_pt = res.forecast_curve[0]
    last_pt = res.forecast_curve[-1]
    assert last_pt.std_dev >= first_pt.std_dev
    assert last_pt.upper_bound_95 > last_pt.lower_bound_95
    assert last_pt.lower_bound_95 == round(last_pt.predicted_soh_pct - 1.96 * last_pt.std_dev, 2)


def test_gpr_cholesky_numerical_stability():
    forecaster = GaussianProcessForecaster()
    # Test identical duplicate points which test jitter ladder
    cycles = [10.0, 10.0, 20.0, 20.0, 30.0, 40.0]
    sohs = [99.5, 99.5, 98.8, 98.8, 98.0, 97.4]

    res = forecaster.forecast("JITTER-TEST", cycles, sohs, forecast_horizon_cycles=50)
    assert res.jitter_applied >= 0.0
    assert len(res.forecast_curve) > 0
