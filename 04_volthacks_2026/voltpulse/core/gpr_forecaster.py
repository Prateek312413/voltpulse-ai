"""
Deterministic Gaussian Process Regression (GPR) Battery SOH/RUL Forecaster with Multi-Kernel Bayesian Uncertainty.
"""

from enum import Enum
import math
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from scipy.spatial.distance import cdist
from scipy.linalg import cholesky, cho_solve
from pydantic import BaseModel, Field


class GPRKernelType(str, Enum):
    MATERN_52 = "MATERN_52"
    MATERN_32 = "MATERN_32"
    RBF = "RBF"
    RATIONAL_QUADRATIC = "RATIONAL_QUADRATIC"
    ARD_COMPOSITE = "ARD_COMPOSITE"


class ForecastPoint(BaseModel):
    cycle: float
    predicted_soh_pct: float
    std_dev: float
    lower_bound_95: float
    upper_bound_95: float
    epistemic_uncertainty: float
    aleatoric_noise: float


class ForecastResult(BaseModel):
    battery_id: str
    selected_kernel: GPRKernelType
    training_points_count: int
    current_cycle: float
    current_soh_pct: float
    target_eol_cycle: Optional[float] = None  # Estimated cycle where SOH <= 80%
    remaining_useful_life_cycles: Optional[float] = None
    forecast_curve: List[ForecastPoint]
    validation_rmse: float
    validation_mae: float
    interval_coverage_pct: float
    jitter_applied: float


class ModelEvaluationResult(BaseModel):
    kernel_type: GPRKernelType
    rmse: float
    mae: float
    coverage_95_pct: float
    log_marginal_likelihood: float
    is_valid: bool
    rank: int = 1


class GaussianProcessForecaster:
    """
    Production-grade Gaussian Process Regression engine engineered for battery degradation.
    Exposes raw covariance matrices, Cholesky solvers, numerical jitter, and uncertainty envelopes.
    """

    def __init__(
        self,
        length_scale: float = 120.0,
        signal_variance: float = 25.0,
        noise_variance: float = 0.04,
        alpha_rq: float = 1.5,
        target_eol_soh: float = 80.0
    ):
        self.length_scale = length_scale
        self.signal_variance = signal_variance
        self.noise_variance = noise_variance
        self.alpha_rq = alpha_rq
        self.target_eol_soh = target_eol_soh

        # Jitter ladder for Cholesky numerical stability
        self.jitter_ladder = [1e-10, 1e-8, 1e-6, 1e-4]

    def _compute_covariance(
        self,
        X1: np.ndarray,
        X2: np.ndarray,
        kernel_type: GPRKernelType
    ) -> np.ndarray:
        """Compute kernel covariance matrix between X1 and X2."""
        dists = cdist(X1, X2, metric='euclidean')

        if kernel_type == GPRKernelType.RBF:
            return self.signal_variance * np.exp(-0.5 * (dists / self.length_scale) ** 2)

        elif kernel_type == GPRKernelType.MATERN_32:
            sqrt3_r = np.sqrt(3.0) * dists / self.length_scale
            return self.signal_variance * (1.0 + sqrt3_r) * np.exp(-sqrt3_r)

        elif kernel_type == GPRKernelType.MATERN_52:
            sqrt5_r = np.sqrt(5.0) * dists / self.length_scale
            return self.signal_variance * (1.0 + sqrt5_r + (5.0 * dists ** 2) / (3.0 * self.length_scale ** 2)) * np.exp(-sqrt5_r)

        elif kernel_type == GPRKernelType.RATIONAL_QUADRATIC:
            base = 1.0 + (dists ** 2) / (2.0 * self.alpha_rq * self.length_scale ** 2)
            return self.signal_variance * np.power(base, -self.alpha_rq)

        elif kernel_type == GPRKernelType.ARD_COMPOSITE:
            # Composite Matérn 5/2 + RBF with linear trend prior
            k1 = self._compute_covariance(X1, X2, GPRKernelType.MATERN_52)
            k2 = self._compute_covariance(X1, X2, GPRKernelType.RBF)
            return 0.7 * k1 + 0.3 * k2

        else:
            return self._compute_covariance(X1, X2, GPRKernelType.MATERN_52)

    def _fit_and_predict(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        kernel_type: GPRKernelType
    ) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """
        Fit GPR via Cholesky decomposition with a linear degradation prior and return (mean, var, log_likelihood, jitter_applied).
        """
        N = len(X_train)

        # 1. Linear Degradation Prior m(x) = y0 + slope * x
        A_train = np.hstack([np.ones((N, 1), dtype=np.float64), X_train])
        trend_coeffs, _, _, _ = np.linalg.lstsq(A_train, y_train, rcond=None)
        m_train = np.dot(A_train, trend_coeffs)

        N_test = len(X_test)
        A_test = np.hstack([np.ones((N_test, 1), dtype=np.float64), X_test])
        m_test = np.dot(A_test, trend_coeffs)

        y_residual = y_train - m_train

        K = self._compute_covariance(X_train, X_train, kernel_type)

        # Cholesky with adaptive jitter
        L = None
        applied_jitter = 0.0
        for jitter in [0.0] + self.jitter_ladder:
            try:
                K_noisy = K + (self.noise_variance + jitter) * np.eye(N)
                L = cholesky(K_noisy, lower=True)
                applied_jitter = jitter
                break
            except np.linalg.LinAlgError:
                continue

        if L is None:
            raise np.linalg.LinAlgError("GPR Covariance Matrix is non-positive definite after maximum jitter.")

        # Solve alpha = K^-1 * y_residual
        alpha = cho_solve((L, True), y_residual)

        # Compute test covariance
        K_star = self._compute_covariance(X_train, X_test, kernel_type)
        K_test = self._compute_covariance(X_test, X_test, kernel_type)

        # Predictive mean with trend prior: mu = m_test + K_star.T * alpha
        mu = m_test + np.dot(K_star.T, alpha)

        # Predictive variance: v = L^-1 * K_star, var = diag(K_test - v.T * v)
        v = np.linalg.solve(L, K_star)
        var = np.diag(K_test) - np.sum(v ** 2, axis=0)
        var = np.maximum(var, 1e-6)  # non-negative variance clamp

        # Log marginal likelihood
        log_likelihood = -0.5 * np.dot(y_residual, alpha) - np.sum(np.log(np.diag(L))) - 0.5 * N * np.log(2.0 * np.pi)

        return mu, var, float(log_likelihood), applied_jitter

    def evaluate_candidate_kernels(
        self,
        cycles: List[float],
        soh_values: List[float],
        val_fraction: float = 0.2
    ) -> List[ModelEvaluationResult]:
        """
        Deterministic cross-validation across all kernel families on temporal split.
        """
        X = np.array(cycles, dtype=np.float64).reshape(-1, 1)
        y = np.array(soh_values, dtype=np.float64)
        N = len(X)

        split_idx = max(5, int(N * (1.0 - val_fraction)))
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_val, y_val = X[split_idx:], y[split_idx:]

        candidates = [
            GPRKernelType.MATERN_52,
            GPRKernelType.MATERN_32,
            GPRKernelType.RBF,
            GPRKernelType.RATIONAL_QUADRATIC,
            GPRKernelType.ARD_COMPOSITE,
        ]

        results: List[ModelEvaluationResult] = []

        for kernel in candidates:
            try:
                mu_val, var_val, log_lik, _ = self._fit_and_predict(X_train, y_train, X_val, kernel)
                std_val = np.sqrt(var_val)

                errors = y_val - mu_val
                rmse = float(np.sqrt(np.mean(errors ** 2)))
                mae = float(np.mean(np.abs(errors)))

                # 95% Coverage: fraction where y_val is within mu +- 1.96*std
                lower = mu_val - 1.96 * std_val
                upper = mu_val + 1.96 * std_val
                covered = np.sum((y_val >= lower) & (y_val <= upper))
                coverage_pct = float((covered / len(y_val)) * 100.0)

                results.append(ModelEvaluationResult(
                    kernel_type=kernel,
                    rmse=round(rmse, 4),
                    mae=round(mae, 4),
                    coverage_95_pct=round(coverage_pct, 2),
                    log_marginal_likelihood=round(log_lik, 3),
                    is_valid=True
                ))
            except Exception:
                results.append(ModelEvaluationResult(
                    kernel_type=kernel,
                    rmse=999.0,
                    mae=999.0,
                    coverage_95_pct=0.0,
                    log_marginal_likelihood=-9999.0,
                    is_valid=False
                ))

        # Deterministic Ranking: Lowest RMSE -> Coverage closest to 95% -> Lower MAE -> Kernel Name
        results.sort(key=lambda r: (
            not r.is_valid,
            r.rmse,
            abs(r.coverage_95_pct - 95.0),
            r.mae,
            r.kernel_type.value
        ))

        for idx, res in enumerate(results):
            res.rank = idx + 1

        return results

    def forecast(
        self,
        battery_id: str,
        cycles: List[float],
        soh_values: Optional[List[float]] = None,
        forecast_horizon_cycles: int = 150,
        preferred_kernel: Optional[GPRKernelType] = None,
        sohs: Optional[List[float]] = None
    ) -> ForecastResult:
        """
        Generate forward-looking SOH trajectory with 95% Bayesian confidence intervals.
        """
        vals = soh_values if soh_values is not None else sohs
        if vals is None:
            raise ValueError("soh_values must be provided.")

        if len(cycles) < 3:
            raise ValueError("At least 3 telemetry observations required for GPR forecasting.")

        # 1. Model evaluation & deterministic selection
        evaluations = self.evaluate_candidate_kernels(cycles, vals)
        selected_kernel = preferred_kernel if preferred_kernel else evaluations[0].kernel_type

        # 2. Fit full dataset
        X_train = np.array(cycles, dtype=np.float64).reshape(-1, 1)
        y_train = np.array(vals, dtype=np.float64)

        current_cycle = float(cycles[-1])
        current_soh = float(vals[-1])

        # Test points: from current cycle to horizon
        test_cycles = np.linspace(current_cycle, current_cycle + forecast_horizon_cycles, 60)
        X_test = test_cycles.reshape(-1, 1)

        mu, var, _, jitter_applied = self._fit_and_predict(X_train, y_train, X_test, selected_kernel)
        std_dev = np.sqrt(var)

        curve: List[ForecastPoint] = []
        target_eol_cycle: Optional[float] = None

        for c, m, s in zip(test_cycles, mu, std_dev):
            m_val = round(float(m), 2)
            s_val = round(float(s), 3)
            lower = round(float(m - 1.96 * s), 2)
            upper = round(float(m + 1.96 * s), 2)

            # Check EOL crossing
            if target_eol_cycle is None and m_val <= self.target_eol_soh:
                target_eol_cycle = round(float(c), 1)

            curve.append(ForecastPoint(
                cycle=round(float(c), 1),
                predicted_soh_pct=m_val,
                std_dev=s_val,
                lower_bound_95=lower,
                upper_bound_95=upper,
                epistemic_uncertainty=round(s_val * 0.8, 3),
                aleatoric_noise=round(math.sqrt(self.noise_variance), 3)
            ))

        rul_cycles = round(target_eol_cycle - current_cycle, 1) if target_eol_cycle else None

        best_eval = next((e for e in evaluations if e.kernel_type == selected_kernel), evaluations[0])

        return ForecastResult(
            battery_id=battery_id,
            selected_kernel=selected_kernel,
            training_points_count=len(cycles),
            current_cycle=current_cycle,
            current_soh_pct=current_soh,
            target_eol_cycle=target_eol_cycle,
            remaining_useful_life_cycles=rul_cycles,
            forecast_curve=curve,
            validation_rmse=best_eval.rmse,
            validation_mae=best_eval.mae,
            interval_coverage_pct=best_eval.coverage_95_pct,
            jitter_applied=jitter_applied
        )
