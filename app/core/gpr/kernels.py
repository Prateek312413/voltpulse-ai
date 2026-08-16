"""
Gaussian Process Kernels for Battery Health Forecasting.
Implements custom mathematical kernels:
- RBF (Radial Basis Function / Squared Exponential)
- Matérn 3/2
- Matérn 5/2
- Rational Quadratic (RQ)
- ARD (Automatic Relevance Determination)
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


def _pairwise_euclidean_distance(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """
    Computes pairwise Euclidean distance matrix between X1 (N x D) and X2 (M x D).
    Returns matrix of shape (N, M).
    """
    X1 = np.atleast_2d(X1)
    X2 = np.atleast_2d(X2)
    # Using stable squared difference
    # (x1 - x2)^2 = x1^2 - 2*x1*x2 + x2^2
    d2 = np.sum(X1**2, axis=1, keepdims=True) - 2 * np.dot(X1, X2.T) + np.sum(X2**2, axis=1, keepdims=True).T
    d2 = np.maximum(d2, 0.0)
    return np.sqrt(d2)


class Kernel(ABC):
    """Abstract base class for all covariance kernels."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for the kernel family."""
        pass

    @abstractmethod
    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Compute the covariance matrix K(X1, X2) given hyperparameter values."""
        pass

    @abstractmethod
    def get_param_names(self, dim: int = 1) -> List[str]:
        """Return list of hyperparameter names."""
        pass

    @abstractmethod
    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        """Return parameter optimization bounds [(min, max), ...]."""
        pass

    @abstractmethod
    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        """Return sensible initial hyperparameter values."""
        pass


class RBFKernel(Kernel):
    """
    Squared Exponential / Radial Basis Function Kernel:
    k(x, x') = sigma_f^2 * exp( - d(x, x')^2 / (2 * length_scale^2) )
    """
    @property
    def name(self) -> str:
        return "RBF"

    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        sigma_f = params.get("sigma_f", 1.0)
        length_scale = params.get("length_scale", 1.0)
        
        # Enforce bounds
        sigma_f = max(sigma_f, 1e-4)
        length_scale = max(length_scale, 1e-4)

        X1 = np.atleast_2d(X1)
        X2 = np.atleast_2d(X2)
        
        # Scaled distance
        X1_scaled = X1 / length_scale
        X2_scaled = X2 / length_scale
        
        d2 = np.sum(X1_scaled**2, axis=1, keepdims=True) - 2 * np.dot(X1_scaled, X2_scaled.T) + np.sum(X2_scaled**2, axis=1, keepdims=True).T
        d2 = np.maximum(d2, 0.0)
        
        return (sigma_f ** 2) * np.exp(-0.5 * d2)

    def get_param_names(self, dim: int = 1) -> List[str]:
        return ["sigma_f", "length_scale"]

    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        return [(1e-3, 5.0), (0.05, 50.0)]

    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        return {"sigma_f": 0.2, "length_scale": 1.0}


class Matern32Kernel(Kernel):
    """
    Matérn 3/2 Kernel:
    k(r) = sigma_f^2 * (1 + sqrt(3)*r / l) * exp(-sqrt(3)*r / l)
    where r = ||x - x'||
    """
    @property
    def name(self) -> str:
        return "Matern32"

    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        sigma_f = max(params.get("sigma_f", 1.0), 1e-4)
        length_scale = max(params.get("length_scale", 1.0), 1e-4)

        dist = _pairwise_euclidean_distance(X1, X2)
        scaled_r = (np.sqrt(3.0) * dist) / length_scale
        return (sigma_f ** 2) * (1.0 + scaled_r) * np.exp(-scaled_r)

    def get_param_names(self, dim: int = 1) -> List[str]:
        return ["sigma_f", "length_scale"]

    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        return [(1e-3, 5.0), (0.05, 50.0)]

    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        return {"sigma_f": 0.2, "length_scale": 1.0}


class Matern52Kernel(Kernel):
    """
    Matérn 5/2 Kernel:
    k(r) = sigma_f^2 * (1 + sqrt(5)*r / l + 5*r^2 / (3*l^2)) * exp(-sqrt(5)*r / l)
    """
    @property
    def name(self) -> str:
        return "Matern52"

    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        sigma_f = max(params.get("sigma_f", 1.0), 1e-4)
        length_scale = max(params.get("length_scale", 1.0), 1e-4)

        dist = _pairwise_euclidean_distance(X1, X2)
        scaled_r = (np.sqrt(5.0) * dist) / length_scale
        scaled_r2 = (5.0 * (dist ** 2)) / (3.0 * (length_scale ** 2))
        return (sigma_f ** 2) * (1.0 + scaled_r + scaled_r2) * np.exp(-scaled_r)

    def get_param_names(self, dim: int = 1) -> List[str]:
        return ["sigma_f", "length_scale"]

    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        return [(1e-3, 5.0), (0.05, 50.0)]

    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        return {"sigma_f": 0.2, "length_scale": 1.0}


class RationalQuadraticKernel(Kernel):
    """
    Rational Quadratic (RQ) Kernel:
    Continuous scale mixture of RBF kernels with different lengthscales:
    k(r) = sigma_f^2 * (1 + r^2 / (2 * alpha * l^2))^(-alpha)
    """
    @property
    def name(self) -> str:
        return "RationalQuadratic"

    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        sigma_f = max(params.get("sigma_f", 1.0), 1e-4)
        length_scale = max(params.get("length_scale", 1.0), 1e-4)
        alpha = max(params.get("alpha", 1.0), 1e-4)

        dist = _pairwise_euclidean_distance(X1, X2)
        factor = 1.0 + (dist ** 2) / (2.0 * alpha * (length_scale ** 2))
        return (sigma_f ** 2) * (factor ** (-alpha))

    def get_param_names(self, dim: int = 1) -> List[str]:
        return ["sigma_f", "length_scale", "alpha"]

    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        return [(1e-3, 5.0), (0.05, 50.0), (1e-2, 10.0)]

    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        return {"sigma_f": 0.2, "length_scale": 1.0, "alpha": 1.0}


class ARDKernel(Kernel):
    """
    Automatic Relevance Determination (ARD) Kernel:
    Assigns an independent lengthscale to each input feature dimension:
    k(x, x') = sigma_f^2 * exp( -0.5 * sum_d ( (x_d - x'_d)^2 / l_d^2 ) )
    Enables direct quantification of feature importance (shorter lengthscale = higher sensitivity).
    """
    @property
    def name(self) -> str:
        return "ARD"

    def compute(self, X1: np.ndarray, X2: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        X1 = np.atleast_2d(X1)
        X2 = np.atleast_2d(X2)
        dim = X1.shape[1]

        sigma_f = max(params.get("sigma_f", 1.0), 1e-4)
        
        # Extract per-dimension lengthscales
        length_scales = np.zeros(dim)
        for d in range(dim):
            length_scales[d] = max(params.get(f"length_scale_{d}", 1.0), 1e-4)

        # Scale features
        X1_scaled = X1 / length_scales
        X2_scaled = X2 / length_scales

        d2 = np.sum(X1_scaled**2, axis=1, keepdims=True) - 2 * np.dot(X1_scaled, X2_scaled.T) + np.sum(X2_scaled**2, axis=1, keepdims=True).T
        d2 = np.maximum(d2, 0.0)

        return (sigma_f ** 2) * np.exp(-0.5 * d2)

    def get_param_names(self, dim: int = 1) -> List[str]:
        names = ["sigma_f"]
        for d in range(dim):
            names.append(f"length_scale_{d}")
        return names

    def default_bounds(self, dim: int = 1) -> List[Tuple[float, float]]:
        bounds = [(1e-3, 5.0)]
        for _ in range(dim):
            bounds.append((0.05, 50.0))
        return bounds

    def default_init_params(self, dim: int = 1) -> Dict[str, float]:
        init = {"sigma_f": 0.2}
        for d in range(dim):
            init[f"length_scale_{d}"] = 1.0
        return init


# Registry of candidate kernels
KERNEL_REGISTRY: Dict[str, Kernel] = {
    "RBF": RBFKernel(),
    "Matern32": Matern32Kernel(),
    "Matern52": Matern52Kernel(),
    "RationalQuadratic": RationalQuadraticKernel(),
    "ARD": ARDKernel()
}
