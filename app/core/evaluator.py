"""
Model Evaluation and Deterministic Selection Hierarchy Engine.
Evaluates candidate GPR kernels and baselines on temporal validation splits,
and deterministically selects the optimal model according to strict tie-break rules.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from app.core.gpr.kernels import KERNEL_REGISTRY, Kernel
from app.core.gpr.gp_engine import fit_and_evaluate_kernel, GPRResult, CustomGaussianProcessRegressor
from app.core.gpr.baselines import fit_and_evaluate_baselines, BaselineResult
from app.core.temporal import create_temporal_validation_split, FeaturePipelineConfig
from app.config import settings


class EvaluationMetricSummary:
    """Stores full validation metrics and diagnostics for a model candidate."""
    def __init__(
        self,
        model_name: str,
        kernel_type: str,
        status: str,
        rmse: Optional[float] = None,
        mae: Optional[float] = None,
        coverage: Optional[float] = None,
        coverage_error: Optional[float] = None,
        log_marginal_likelihood: Optional[float] = None,
        jitter_used: float = 0.0,
        hyperparameters: Optional[Dict[str, float]] = None,
        elapsed_seconds: float = 0.0,
        error_message: Optional[str] = None,
        is_selected: bool = False,
        selection_rank: int = 999
    ):
        self.model_name = model_name
        self.kernel_type = kernel_type
        self.status = status
        self.rmse = rmse
        self.mae = mae
        self.coverage = coverage
        self.coverage_error = coverage_error
        self.log_marginal_likelihood = log_marginal_likelihood
        self.jitter_used = jitter_used
        self.hyperparameters = hyperparameters or {}
        self.elapsed_seconds = elapsed_seconds
        self.error_message = error_message
        self.is_selected = is_selected
        self.selection_rank = selection_rank

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "kernel_type": self.kernel_type,
            "status": self.status,
            "rmse": float(self.rmse) if self.rmse is not None else None,
            "mae": float(self.mae) if self.mae is not None else None,
            "coverage": float(self.coverage) if self.coverage is not None else None,
            "coverage_error": float(self.coverage_error) if self.coverage_error is not None else None,
            "log_marginal_likelihood": float(self.log_marginal_likelihood) if self.log_marginal_likelihood is not None else None,
            "jitter_used": self.jitter_used,
            "hyperparameters": self.hyperparameters,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "error_message": self.error_message,
            "is_selected": self.is_selected,
            "selection_rank": self.selection_rank
        }


def _compute_metrics(
    y_true: np.ndarray,
    mu: np.ndarray,
    lower_ci: np.ndarray,
    upper_ci: np.ndarray,
    target_coverage: float = 0.95
) -> Tuple[float, float, float, float]:
    """Computes RMSE, MAE, Coverage, and Coverage Error against target."""
    diff = y_true - mu
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    mae = float(np.mean(np.abs(diff)))
    
    in_interval = (y_true >= lower_ci) & (y_true <= upper_ci)
    coverage = float(np.mean(in_interval))
    coverage_error = float(abs(coverage - target_coverage))
    
    return rmse, mae, coverage, coverage_error


def evaluate_candidate_models(
    X: np.ndarray,
    y: np.ndarray,
    target_coverage: float = 0.95,
    include_baselines: bool = True
) -> Tuple[List[EvaluationMetricSummary], EvaluationMetricSummary]:
    """
    Evaluates candidate kernels and baselines using a deterministic temporal split.
    Ranks them according to the PRD deterministic tie-break hierarchy:
    
    Tier 1: Valid Execution (status == "SUCCESS" before "FAILED")
    Tier 2: Lower Validation RMSE (tolerance 1e-6)
    Tier 3: Prediction-interval coverage closer to target (|coverage - 0.95|)
    Tier 4: Lower Validation MAE (tolerance 1e-6)
    Tier 5: Alphabetical kernel name tie-breaker.
    
    Returns (all_candidate_summaries, best_selected_model).
    """
    X_train, y_train, X_val, y_val = create_temporal_validation_split(
        X, y, train_ratio=settings.TRAIN_SPLIT_RATIO
    )

    summaries: List[EvaluationMetricSummary] = []

    # 1. Evaluate GPR Kernels
    candidate_kernel_names = ["RBF", "Matern32", "Matern52", "RationalQuadratic", "ARD"]
    
    for k_name in candidate_kernel_names:
        kernel = KERNEL_REGISTRY[k_name]
        gpr_res: GPRResult = fit_and_evaluate_kernel(kernel, X_train, y_train, X_val)
        
        if gpr_res.status == "SUCCESS" and gpr_res.mu is not None and gpr_res.lower_ci is not None:
            rmse, mae, cov, cov_err = _compute_metrics(
                y_val, gpr_res.mu, gpr_res.lower_ci, gpr_res.upper_ci, target_coverage
            )
            summaries.append(EvaluationMetricSummary(
                model_name=f"GPR ({k_name})",
                kernel_type=k_name,
                status="SUCCESS",
                rmse=rmse,
                mae=mae,
                coverage=cov,
                coverage_error=cov_err,
                log_marginal_likelihood=gpr_res.log_marginal_likelihood,
                jitter_used=gpr_res.jitter_used,
                hyperparameters=gpr_res.params,
                elapsed_seconds=gpr_res.elapsed_seconds
            ))
        else:
            summaries.append(EvaluationMetricSummary(
                model_name=f"GPR ({k_name})",
                kernel_type=k_name,
                status="FAILED",
                jitter_used=gpr_res.jitter_used,
                hyperparameters=gpr_res.params,
                error_message=gpr_res.error_message or "Decomposition or optimization failed",
                elapsed_seconds=gpr_res.elapsed_seconds
            ))

    # 2. Evaluate Non-GPR Baselines for comparison (optional)
    if include_baselines:
        baseline_results = fit_and_evaluate_baselines(X_train, y_train, X_val, y_val)
        for b_name, b_res in baseline_results.items():
            if b_res.status == "SUCCESS":
                cov_err = float(abs(b_res.coverage - target_coverage)) if b_res.coverage is not None else 1.0
                summaries.append(EvaluationMetricSummary(
                    model_name=b_res.model_name,
                    kernel_type=b_name,
                    status="SUCCESS",
                    rmse=b_res.rmse,
                    mae=b_res.mae,
                    coverage=b_res.coverage,
                    coverage_error=cov_err,
                    elapsed_seconds=b_res.elapsed_seconds
                ))
            else:
                summaries.append(EvaluationMetricSummary(
                    model_name=b_res.model_name,
                    kernel_type=b_name,
                    status="FAILED",
                    error_message=b_res.error_message,
                    elapsed_seconds=b_res.elapsed_seconds
                ))

    # 3. Deterministic Sorting Key Function
    # Focus selection primarily on GPR candidate kernels as per PRD
    def _model_sort_key(item: EvaluationMetricSummary):
        is_gpr = item.kernel_type in KERNEL_REGISTRY
        # Prefer valid GPR candidates
        status_rank = 0 if (item.status == "SUCCESS" and is_gpr) else (1 if item.status == "SUCCESS" else 2)
        rmse_val = round(item.rmse, 6) if item.rmse is not None else 1e9
        cov_err_val = round(item.coverage_error, 6) if item.coverage_error is not None else 1e9
        mae_val = round(item.mae, 6) if item.mae is not None else 1e9
        name_val = item.kernel_type
        return (status_rank, rmse_val, cov_err_val, mae_val, name_val)

    sorted_summaries = sorted(summaries, key=_model_sort_key)

    # Assign ranks and mark selected
    for idx, item in enumerate(sorted_summaries):
        item.selection_rank = idx + 1
        item.is_selected = (idx == 0)

    best_model = sorted_summaries[0]
    return sorted_summaries, best_model
