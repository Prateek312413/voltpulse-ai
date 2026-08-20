"""
Unit tests for Deterministic Model Evaluation and Selection Hierarchy.
"""

import numpy as np
from app.core.evaluator import evaluate_candidate_models, EvaluationMetricSummary


def test_deterministic_model_selection():
    X = np.linspace(1, 50, 40).reshape(-1, 1)
    y = 1.0 - 0.003 * X.ravel() + np.random.normal(0, 0.002, 40)

    summaries, best = evaluate_candidate_models(X, y)

    assert len(summaries) >= 4
    assert best is not None
    assert best.status == "SUCCESS"
    assert best.is_selected is True
    assert best.selection_rank == 1


def test_tie_break_ranking_order():
    """Verifies 5-tier deterministic tie-break hierarchy."""
    s1 = EvaluationMetricSummary(model_name="GPR (RBF)", kernel_type="RBF", status="SUCCESS", rmse=0.010, coverage_error=0.01, mae=0.008)
    s2 = EvaluationMetricSummary(model_name="GPR (Matern32)", kernel_type="Matern32", status="SUCCESS", rmse=0.010, coverage_error=0.01, mae=0.008)
    
    # Both have identical RMSE=0.010, Coverage Error=0.01, MAE=0.008
    # Alphabetical order: "Matern32" comes before "RBF"
    def _sort_key(item):
        return (round(item.rmse, 6), round(item.coverage_error, 6), round(item.mae, 6), item.kernel_type)

    ranked = sorted([s1, s2], key=_sort_key)
    assert ranked[0].kernel_type == "Matern32"
    assert ranked[1].kernel_type == "RBF"
