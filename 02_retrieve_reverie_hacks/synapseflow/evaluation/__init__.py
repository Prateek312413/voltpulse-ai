"""
SynapseFlow Evaluation & Benchmark Suite
Compares Single-Prompt Baselines vs Multi-Stage SynapseFlow across 5 complex test cases.
"""
from .benchmark import BenchmarkRunner
from .metrics import compute_comparison_metrics

__all__ = ["BenchmarkRunner", "compute_comparison_metrics"]
