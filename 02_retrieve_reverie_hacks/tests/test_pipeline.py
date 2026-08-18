"""
End-to-End Pipeline Execution Tests
"""

import pytest
from synapseflow.pipeline.orchestrator import PipelineOrchestrator
from synapseflow.models import PipelineExecutionRequest

@pytest.fixture
def orchestrator():
    return PipelineOrchestrator()

def test_full_pipeline_engineering_prompt(orchestrator):
    req = PipelineExecutionRequest(
        prompt="Calculate Arrhenius degradation and Joule heating for 40C battery with 15A current.",
        domain="engineering",
        human_in_the_loop_mode=False,
        strict_verification=True
    )
    res = orchestrator.run(req)
    
    assert res.pipeline_id.startswith("flow_")
    assert len(res.subtasks) >= 2
    assert len(res.stage_traces) == 5
    assert res.confidence_score >= 0.85
    assert len(res.final_output) > 50
    assert res.total_latency_ms > 0

def test_full_pipeline_clinical_prompt(orchestrator):
    req = PipelineExecutionRequest(
        prompt="Derive antibiotic half-life given CL = 4.8 L/h and Vd = 38 L for renal patient.",
        domain="clinical",
        human_in_the_loop_mode=False,
        strict_verification=True
    )
    res = orchestrator.run(req)
    assert res.domain == "clinical"
    assert len(res.stage_traces) == 5
    assert res.confidence_score > 0.80
