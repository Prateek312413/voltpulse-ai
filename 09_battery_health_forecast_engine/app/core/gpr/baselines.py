"""
Baseline Regression Models for Comparative Benchmarking against Gaussian Process Regression:
- Polynomial Regression (Degree 2)
- K-Nearest Neighbors Regressor (KNN)
- Decision Tree Regressor
"""

import time
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
from typing import Dict, Any, Tuple, Optional
from app.config import settings


class BaselineResult:
    def __init__(
        self,
        model_name: str,
        status: str,
        mu: Optional[np.ndarray] = None,
        sigma: Optional[np.ndarray] = None,
        lower_ci: Optional[np.ndarray] = None,
        upper_ci: Optional[np.ndarray] = None,
        rmse: Optional[float] = None,
        mae: Optional[float] = None,
        coverage: Optional[float] = None,
        elapsed_seconds: float = 0.0,
        error_message: Optional[str] = None
    ):
        self.model_name = model_name
        self.status = status
        self.mu = mu
        self.sigma = sigma
        self.lower_ci = lower_ci
        self.upper_ci = upper_ci
        self.rmse = rmse
        self.mae = mae
        self.coverage = coverage
        self.elapsed_seconds = elapsed_seconds
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "status": self.status,
            "rmse": self.rmse,
            "mae": self.mae,
            "coverage": self.coverage,
            "elapsed_seconds": self.elapsed_seconds,
            "error_message": self.error_message
        }


def fit_and_evaluate_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray
) -> Dict[str, BaselineResult]:
    """Fits Polynomial, KNN, and Decision Tree baselines and returns their validation results."""
    results = {}
    z = settings.CI_Z_SCORE

    # 1. Polynomial Regression (Degree 2 Ridge)
    t0 = time.time()
    try:
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly_train = poly.fit_transform(X_train)
        X_poly_val = poly.transform(X_val)
        
        reg = Ridge(alpha=1.0)
        reg.fit(X_poly_train, y_train)
        
        y_pred_train = reg.predict(X_poly_train)
        residuals = y_train - y_pred_train
        res_std = float(np.std(residuals)) if len(residuals) > 1 else 0.05
        
        mu = reg.predict(X_poly_val)
        sigma = np.full_like(mu, res_std)
        lower_ci = mu - z * sigma
        upper_ci = mu + z * sigma
        
        rmse = float(np.sqrt(np.mean((y_val - mu) ** 2)))
        mae = float(np.mean(np.abs(y_val - mu)))
        coverage = float(np.mean((y_val >= lower_ci) & (y_val <= upper_ci)))
        
        results["PolynomialRegression"] = BaselineResult(
            model_name="PolynomialRegression (Deg 2)",
            status="SUCCESS",
            mu=mu,
            sigma=sigma,
            lower_ci=lower_ci,
            upper_ci=upper_ci,
            rmse=rmse,
            mae=mae,
            coverage=coverage,
            elapsed_seconds=time.time() - t0
        )
    except Exception as e:
        results["PolynomialRegression"] = BaselineResult(
            model_name="PolynomialRegression (Deg 2)",
            status="FAILED",
            error_message=str(e),
            elapsed_seconds=time.time() - t0
        )

    # 2. K-Nearest Neighbors
    t0 = time.time()
    try:
        n_neighbors = min(5, max(1, len(X_train) - 1))
        knn = KNeighborsRegressor(n_neighbors=n_neighbors, weights="distance")
        knn.fit(X_train, y_train)
        
        y_pred_train = knn.predict(X_train)
        residuals = y_train - y_pred_train
        res_std = float(np.std(residuals)) if len(residuals) > 1 else 0.05
        
        mu = knn.predict(X_val)
        sigma = np.full_like(mu, res_std)
        lower_ci = mu - z * sigma
        upper_ci = mu + z * sigma
        
        rmse = float(np.sqrt(np.mean((y_val - mu) ** 2)))
        mae = float(np.mean(np.abs(y_val - mu)))
        coverage = float(np.mean((y_val >= lower_ci) & (y_val <= upper_ci)))
        
        results["KNN"] = BaselineResult(
            model_name="K-Nearest Neighbors",
            status="SUCCESS",
            mu=mu,
            sigma=sigma,
            lower_ci=lower_ci,
            upper_ci=upper_ci,
            rmse=rmse,
            mae=mae,
            coverage=coverage,
            elapsed_seconds=time.time() - t0
        )
    except Exception as e:
        results["KNN"] = BaselineResult(
            model_name="K-Nearest Neighbors",
            status="FAILED",
            error_message=str(e),
            elapsed_seconds=time.time() - t0
        )

    # 3. Decision Tree Regressor
    t0 = time.time()
    try:
        dt = DecisionTreeRegressor(max_depth=4, random_state=42)
        dt.fit(X_train, y_train)
        
        y_pred_train = dt.predict(X_train)
        residuals = y_train - y_pred_train
        res_std = float(np.std(residuals)) if len(residuals) > 1 else 0.05
        
        mu = dt.predict(X_val)
        sigma = np.full_like(mu, res_std)
        lower_ci = mu - z * sigma
        upper_ci = mu + z * sigma
        
        rmse = float(np.sqrt(np.mean((y_val - mu) ** 2)))
        mae = float(np.mean(np.abs(y_val - mu)))
        coverage = float(np.mean((y_val >= lower_ci) & (y_val <= upper_ci)))
        
        results["DecisionTree"] = BaselineResult(
            model_name="Decision Tree",
            status="SUCCESS",
            mu=mu,
            sigma=sigma,
            lower_ci=lower_ci,
            upper_ci=upper_ci,
            rmse=rmse,
            mae=mae,
            coverage=coverage,
            elapsed_seconds=time.time() - t0
        )
    except Exception as e:
        results["DecisionTree"] = BaselineResult(
            model_name="Decision Tree",
            status="FAILED",
            error_message=str(e),
            elapsed_seconds=time.time() - t0
        )

    return results
