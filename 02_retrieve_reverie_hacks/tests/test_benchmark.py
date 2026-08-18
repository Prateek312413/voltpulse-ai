"""
Benchmark & Metrics Validation Tests
"""

import pytest
from synapseflow.pipeline.orchestrator import PipelineOrchestrator
from synapseflow.evaluation.benchmark import BenchmarkRunner
from synapseflow.evaluation.metrics import compute_comparison_metrics
from synapseflow.models import (
    SinglePromptBaselineResult,
    PipelineExecutionResponse,
    PipelineExecutionRequest
)

def test_benchmark_runner():
    orchestrator = PipelineOrchestrator()
    runner = BenchmarkRunner(orchestrator)
    results = runner.run_all()
    
    assert len(results) == 5
    for r in results:
        assert r.test_case_id.startswith("TC_")
        assert r.single_prompt_baseline.hallucination_rate > 0
        assert r.synapseflow_workflow.confidence_score >= 0.80
        assert "mathematical_accuracy" in r.improvement_summary
        assert r.improvement_summary["mathematical_accuracy"]["synapseflow_workflow_pct"] >= 90.0

def test_metrics_computation():
    baseline = SinglePromptBaselineResult(
        model_name="Baseline",
        raw_response="Random approximation with 15 * 0.042 = 0.63",
        accuracy_score=0.35,
        hallucination_rate=65.0,
        latency_ms=450.0,
        structural_validity=False,
        verified_math_error_count=2
    )
    
    orchestrator = PipelineOrchestrator()
    req = PipelineExecutionRequest(prompt="Test prompt", domain="engineering")
    workflow = orchestrator.run(req)
    
    metrics = compute_comparison_metrics(baseline, workflow, ["Joule loss 9.45W", "Arrhenius rate"])
    assert metrics["mathematical_accuracy"]["improvement_pct"] > 0
    assert metrics["hallucination_rate"]["reduction_pct"] > 0
