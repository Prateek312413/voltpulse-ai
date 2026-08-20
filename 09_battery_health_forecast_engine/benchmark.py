"""
Comprehensive Benchmark Suite for Uncertainty-Aware Battery Health Forecast Engine.
Compares GPR Kernel Families (RBF, Matern 3/2, Matern 5/2, Rational Quadratic, ARD)
and Non-GPR Baselines (Polynomial, KNN, Decision Tree) across Accuracy, Uncertainty, and Latency.
"""

import time
import numpy as np

from data.generator import generate_battery_telemetry
from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models
from app.core.forecaster import generate_forecast
from app.core.gpr.kernels import KERNEL_REGISTRY
from app.core.gpr.gp_engine import CustomGaussianProcessRegressor


def run_benchmarks():
    print("=" * 80)
    print("  BATTERY HEALTH FORECAST ENGINE - GPR KERNEL & LATENCY BENCHMARK SUITE")
    print("=" * 80)

    # Generate 120 cycles synthetic telemetry
    bat_id = "BENCHMARK-BAT-18650"
    raw_obs = generate_battery_telemetry(bat_id, num_cycles=120)
    
    print(f"[*] Dataset: {len(raw_obs)} sequential battery cycles")
    print("[*] Splitting: 75% Chronological Train / 25% Chronological Holdout")
    print("-" * 80)

    _, cfg, X, y = build_active_temporal_dataset(raw_obs)

    # 1. Candidate Kernel Evaluation
    start_eval = time.perf_counter()
    summaries, best_model = evaluate_candidate_models(X, y, target_coverage=0.95, include_baselines=True)
    eval_duration = (time.perf_counter() - start_eval) * 1000.0

    table_data = []
    for s in summaries:
        table_data.append([
            s.selection_rank,
            s.model_name,
            s.status,
            f"{s.rmse:.6f}" if s.rmse is not None else "N/A",
            f"{s.mae:.6f}" if s.mae is not None else "N/A",
            f"{s.coverage*100:.1f}%" if s.coverage is not None else "N/A",
            f"{s.coverage_error*100:.2f}%" if s.coverage_error is not None else "N/A",
            f"{s.jitter_used:.0e}" if s.jitter_used > 0 else "0.0",
            f"{s.elapsed_seconds*1000:.2f} ms",
            "SELECTED" if s.is_selected else "-"
        ])

    headers = ["Rank", "Model / Kernel", "Status", "RMSE", "MAE", "95% Coverage", "Cov Delta", "Jitter", "Latency", "Verdict"]
    
    try:
        from tabulate import tabulate
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    except Exception:
        header_line = " | ".join(headers)
        print(header_line)
        print("-" * len(header_line))
        for row in table_data:
            print(" | ".join(str(c) for c in row))

    print("-" * 80)
    print(f"[+] Winner Candidate: {best_model.model_name} (RMSE: {best_model.rmse:.6f}, MAE: {best_model.mae:.6f})")
    print(f"[+] Total Evaluation Time: {eval_duration:.2f} ms")
    print("=" * 80)

    # 2. Multi-Horizon Forecast Latency & Uncertainty Cone Test
    print("[*] Testing Multi-Horizon Forecast Projection (Cycles 121 -> 180)...")
    t0 = time.perf_counter()
    fc_result = generate_forecast(X, y, cfg, target_cycle=180, selected_kernel_name=best_model.kernel_type, telemetry_version=1)
    fc_lat = (time.perf_counter() - t0) * 1000.0

    print(f"[+] Forecast at Target Cycle 180: SOH = {fc_result.predicted_soh:.4f} +/- {1.96*fc_result.std_dev:.4f}")
    print(f"[+] 95% Confidence Interval: [{fc_result.lower_ci:.4f}, {fc_result.upper_ci:.4f}]")
    print(f"[+] Forecast Generation Latency: {fc_lat:.2f} ms")
    print(f"[+] Multi-Horizon Points Calculated: {len(fc_result.multi_horizon_points)} steps")
    print("=" * 80)
    print("[SUCCESS] All GPR benchmarks completed successfully!")


if __name__ == "__main__":
    run_benchmarks()
