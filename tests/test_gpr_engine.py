"""
Unit tests for Gaussian Process Regression Mathematics, Kernels, and Jitter Ladder.
"""

import numpy as np
import pytest
from app.core.gpr.kernels import (
    RBFKernel,
    Matern32Kernel,
    Matern52Kernel,
    RationalQuadraticKernel,
    ARDKernel
)
from app.core.gpr.gp_engine import (
    CustomGaussianProcessRegressor,
    fit_and_evaluate_kernel
)


def test_kernel_properties_and_shapes():
    X1 = np.array([[1.0], [2.0], [3.0]])
    X2 = np.array([[1.5], [2.5]])

    kernels = [RBFKernel(), Matern32Kernel(), Matern52Kernel(), RationalQuadraticKernel()]
    for k in kernels:
        K = k.compute(X1, X2, {"sigma_f": 1.0, "length_scale": 1.0, "alpha": 1.0})
        assert K.shape == (3, 2)
        # Self covariance must be symmetric and positive diagonal
        K_self = k.compute(X1, X1, {"sigma_f": 1.0, "length_scale": 1.0, "alpha": 1.0})
        assert K_self.shape == (3, 3)
        assert np.allclose(K_self, K_self.T)
        assert np.all(np.diag(K_self) > 0.0)


def test_ard_multi_dimensional_kernel():
    X = np.array([
        [1.0, 3.7, 25.0],
        [2.0, 3.68, 26.0],
        [3.0, 3.65, 27.5]
    ])
    ard = ARDKernel()
    params = {"sigma_f": 0.8, "length_scale_0": 1.0, "length_scale_1": 0.5, "length_scale_2": 2.0}
    K = ard.compute(X, X, params)
    assert K.shape == (3, 3)
    assert np.allclose(K, K.T)


def test_gpr_fit_predict_confidence_intervals():
    X = np.linspace(0, 10, 20).reshape(-1, 1)
    y = 1.0 - 0.02 * X.ravel() + 0.005 * np.sin(X.ravel())

    gpr = CustomGaussianProcessRegressor(kernel=RBFKernel(), noise_variance=1e-4)
    gpr.fit(X, y)
    assert gpr.is_fitted is True
    assert gpr.log_marginal_likelihood is not None

    X_test = np.array([[5.0], [12.0]])
    mu, std, lower_ci, upper_ci = gpr.predict(X_test, return_std=True)

    assert len(mu) == 2
    assert len(std) == 2
    # Confidence bounds sanity
    assert lower_ci[0] < mu[0] < upper_ci[0]
    assert lower_ci[1] < mu[1] < upper_ci[1]
    # Extrapolation uncertainty at cycle 12 must be strictly greater than interpolation uncertainty at cycle 5
    assert std[1] > std[0]


def test_jitter_ladder_numerical_recovery():
    """Verifies that the bounded jitter ladder rescues an ill-conditioned covariance matrix."""
    # Strictly collinear / duplicate points induce exact zero eigenvalue (singularity)
    X_singular = np.array([[1.0], [1.0], [1.0], [2.0], [3.0]])
    y = np.array([1.0, 1.0, 1.0, 0.9, 0.8])

    gpr = CustomGaussianProcessRegressor(kernel=RBFKernel(), noise_variance=0.0, optimize_hyperparameters=False)
    gpr.fit(X_singular, y)

    assert gpr.is_fitted is True
    # Jitter ladder must have been activated (> 0)
    assert gpr.jitter_used >= 1e-10
