"""
Gaussian Process Regression Engine with Explicit Cholesky Decomposition
and Deterministic Jitter Ladder for Numerical Stability.

Exposes exact mathematical steps:
1. Prior Covariance Matrix Construction
2. Deterministic Bounded Jitter Ladder [0.0, 1e-10, 1e-8, 1e-6, 1e-4]
3. Cholesky Factorization L * L^T = K
4. Exact Negative Log Marginal Likelihood Optimization
5. Triangular Solves for Posterior Mean and Covariance
"""

import time
import numpy as np
from scipy.linalg import cholesky, solve_triangular, LinAlgError
from scipy.optimize import minimize
from typing import Dict, List, Optional, Tuple, Any

from app.core.gpr.kernels import Kernel, KERNEL_REGISTRY, RBFKernel
from app.config import settings


class GPRResult:
    """Stores full evaluation and forecast results from Gaussian Process Regression."""
    def __init__(
        self,
        kernel_name: str,
        status: str,
        params: Dict[str, float],
        noise_variance: float,
        jitter_used: float,
        log_marginal_likelihood: Optional[float] = None,
        condition_estimate: Optional[float] = None,
        error_message: Optional[str] = None,
        mu: Optional[np.ndarray] = None,
        sigma: Optional[np.ndarray] = None,
        lower_ci: Optional[np.ndarray] = None,
        upper_ci: Optional[np.ndarray] = None,
        elapsed_seconds: float = 0.0
    ):
        self.kernel_name = kernel_name
        self.status = status  # "SUCCESS" or "FAILED"
        self.params = params
        self.noise_variance = noise_variance
        self.jitter_used = jitter_used
        self.log_marginal_likelihood = log_marginal_likelihood
        self.condition_estimate = condition_estimate
        self.error_message = error_message
        self.mu = mu
        self.sigma = sigma
        self.lower_ci = lower_ci
        self.upper_ci = upper_ci
        self.elapsed_seconds = elapsed_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kernel_name": self.kernel_name,
            "status": self.status,
            "params": self.params,
            "noise_variance": self.noise_variance,
            "jitter_used": self.jitter_used,
            "log_marginal_likelihood": float(self.log_marginal_likelihood) if self.log_marginal_likelihood is not None else None,
            "condition_estimate": float(self.condition_estimate) if self.condition_estimate is not None else None,
            "error_message": self.error_message,
            "elapsed_seconds": self.elapsed_seconds
        }


class CustomGaussianProcessRegressor:
    """
    Explicit, transparent Gaussian Process Regressor.
    Follows Rasmussen & Williams (2006) Algorithm 2.1.
    """

    def __init__(
        self,
        kernel: Optional[Kernel] = None,
        noise_variance: float = 1e-4,
        jitter_sequence: Optional[List[float]] = None,
        optimize_hyperparameters: bool = True
    ):
        self.kernel = kernel or RBFKernel()
        self.noise_variance = noise_variance
        self.jitter_sequence = jitter_sequence or settings.JITTER_SEQUENCE
        self.optimize_hyperparameters = optimize_hyperparameters

        # Fitted attributes
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_mean: float = 0.0
        self.L: Optional[np.ndarray] = None  # Cholesky factor of K
        self.alpha: Optional[np.ndarray] = None  # L^T \ (L \ (y - y_mean))
        self.params: Dict[str, float] = {}
        self.jitter_used: float = 0.0
        self.log_marginal_likelihood: Optional[float] = None
        self.is_fitted: bool = False

    def _decompose_covariance(
        self,
        K: np.ndarray
    ) -> Tuple[np.ndarray, float, float]:
        """
        Applies deterministic jitter ladder to decompose covariance matrix K = L L^T.
        Returns (L, jitter_applied, condition_estimate).
        Raises LinAlgError if decomposition fails even after max jitter.
        """
        N = K.shape[0]
        I = np.eye(N)
        last_error = None

        for jitter in self.jitter_sequence:
            try:
                K_jittered = K + (jitter * I)
                # Compute Cholesky lower triangular L
                L = cholesky(K_jittered, lower=True)
                
                # Approximate condition number from diagonal ratio
                diag_L = np.diag(L)
                min_diag = np.min(np.abs(diag_L))
                max_diag = np.max(np.abs(diag_L))
                cond_est = (max_diag / min_diag) ** 2 if min_diag > 1e-15 else 1e12
                
                return L, jitter, cond_est
            except LinAlgError as e:
                last_error = e
                continue

        raise LinAlgError(f"Decomposition failed after attempting jitter ladder {self.jitter_sequence}. Error: {last_error}")

    def _negative_log_marginal_likelihood(
        self,
        param_vector: np.ndarray,
        param_names: List[str],
        X: np.ndarray,
        y: np.ndarray
    ) -> float:
        """
        Evaluates negative log marginal likelihood:
        -log p(y|X, theta) = 0.5 * y^T * alpha + sum(log(diag(L))) + 0.5 * N * log(2*pi)
        """
        params = {name: float(val) for name, val in zip(param_names, param_vector)}
        sigma_n2 = max(params.pop("noise_variance", self.noise_variance), 1e-6)

        try:
            # 1. Prior Covariance
            K = self.kernel.compute(X, X, params) + sigma_n2 * np.eye(X.shape[0])
            
            # 2. Cholesky
            L, _, _ = self._decompose_covariance(K)
            
            # 3. Solve L * v = y
            v = solve_triangular(L, y, lower=True)
            
            # 4. alpha = L^T \ v
            alpha = solve_triangular(L.T, v, lower=False)
            
            # 5. NLML
            N = X.shape[0]
            data_fit = 0.5 * np.dot(y, alpha)
            complexity_penalty = np.sum(np.log(np.diag(L)))
            normalization = 0.5 * N * np.log(2.0 * np.pi)
            
            nlml = data_fit + complexity_penalty + normalization
            if np.isnan(nlml) or np.isinf(nlml):
                return 1e9
            return float(nlml)
        except Exception:
            return 1e9

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        initial_params: Optional[Dict[str, float]] = None
    ) -> "CustomGaussianProcessRegressor":
        """
        Fits the GPR model on training data (X, y).
        """
        X = np.atleast_2d(X)
        y = np.asarray(y).ravel()
        dim = X.shape[1]
        N = X.shape[0]

        if N == 0:
            raise ValueError("Training dataset contains 0 observations.")

        self.X_train = X.copy()
        self.y_mean = float(np.mean(y))
        self.y_train = y - self.y_mean  # Center targets

        param_names = self.kernel.get_param_names(dim)
        
        # Optimize hyperparameters if requested
        if self.optimize_hyperparameters and N >= 4:
            init_dict = initial_params or self.kernel.default_init_params(dim)
            init_vec = [init_dict.get(name, 1.0) for name in param_names]
            bounds = self.kernel.default_bounds(dim)

            # Optimization using L-BFGS-B
            res = minimize(
                fun=self._negative_log_marginal_likelihood,
                x0=init_vec,
                args=(param_names, self.X_train, self.y_train),
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 150, "ftol": 1e-6}
            )

            if res.success or res.fun < 1e8:
                self.params = {name: float(val) for name, val in zip(param_names, res.x)}
            else:
                self.params = init_dict
        else:
            self.params = initial_params or self.kernel.default_init_params(dim)

        # Build final covariance matrix
        K = self.kernel.compute(self.X_train, self.X_train, self.params) + (self.noise_variance * np.eye(N))
        
        # Factorize with jitter ladder
        self.L, self.jitter_used, cond = self._decompose_covariance(K)

        # Solve alpha
        v = solve_triangular(self.L, self.y_train, lower=True)
        self.alpha = solve_triangular(self.L.T, v, lower=False)

        # Compute final log marginal likelihood
        data_fit = 0.5 * np.dot(self.y_train, self.alpha)
        complexity = np.sum(np.log(np.diag(self.L)))
        norm = 0.5 * N * np.log(2.0 * np.pi)
        self.log_marginal_likelihood = -(data_fit + complexity + norm)
        
        self.is_fitted = True
        return self

    def predict(
        self,
        X_star: np.ndarray,
        return_std: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Computes predictive mean and confidence bounds for query locations X_star.
        Returns (mu, std, lower_ci, upper_ci).
        """
        if not self.is_fitted or self.L is None or self.alpha is None:
            raise RuntimeError("GPR model must be fitted before predict() is called.")

        X_star = np.atleast_2d(X_star)
        
        # Cross covariance k_* = K(X_train, X_star)
        k_star = self.kernel.compute(self.X_train, X_star, self.params)  # shape (N, M)
        
        # Posterior mean: mu_* = k_*^T * alpha + y_mean
        f_mean = np.dot(k_star.T, self.alpha) + self.y_mean
        
        if not return_std:
            return f_mean, None, None, None

        # Solve v = L \ k_*
        v = solve_triangular(self.L, k_star, lower=True)  # shape (N, M)
        
        # Self covariance diag(K(X_star, X_star))
        k_star_star = self.kernel.compute(X_star, X_star, self.params)
        diag_k_star_star = np.diag(k_star_star)
        
        # Epistemic variance: k(x*, x*) - v^T v
        epistemic_var = diag_k_star_star - np.sum(v**2, axis=0)
        epistemic_var = np.maximum(epistemic_var, 0.0)
        
        # Total predictive variance includes observation noise
        total_var = epistemic_var + self.noise_variance
        std = np.sqrt(total_var)
        
        # 95% Confidence bounds
        z = settings.CI_Z_SCORE
        lower_ci = f_mean - z * std
        upper_ci = f_mean + z * std
        
        return f_mean, std, lower_ci, upper_ci


def fit_and_evaluate_kernel(
    kernel: Kernel,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    noise_variance: float = 1e-4
) -> GPRResult:
    """
    Safely fits a candidate kernel on training data and computes predictions on validation data.
    Gracefully handles numerical instability without raising unhandled exceptions.
    """
    start_time = time.time()
    try:
        model = CustomGaussianProcessRegressor(
            kernel=kernel,
            noise_variance=noise_variance,
            optimize_hyperparameters=True
        )
        model.fit(X_train, y_train)
        
        # Predict on validation
        mu, std, lower_ci, upper_ci = model.predict(X_val, return_std=True)
        
        elapsed = time.time() - start_time
        return GPRResult(
            kernel_name=kernel.name,
            status="SUCCESS",
            params=model.params,
            noise_variance=model.noise_variance,
            jitter_used=model.jitter_used,
            log_marginal_likelihood=model.log_marginal_likelihood,
            mu=mu,
            sigma=std,
            lower_ci=lower_ci,
            upper_ci=upper_ci,
            elapsed_seconds=elapsed
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return GPRResult(
            kernel_name=kernel.name,
            status="FAILED",
            params={},
            noise_variance=noise_variance,
            jitter_used=0.0,
            error_message=str(e),
            elapsed_seconds=elapsed
        )
