"""
Unit Tests for Individual SynapseFlow Pipeline Stages
"""

import pytest
from synapseflow.config import settings
from synapseflow.clients.featherless_client import FeatherlessClient
from synapseflow.clients.wolfram_client import WolframClient
from synapseflow.pipeline.stage1_decompose import Stage1Decomposition
from synapseflow.pipeline.stage2_reason import Stage2Reasoning
from synapseflow.pipeline.stage3_verify import Stage3Verification
from synapseflow.pipeline.stage4_consensus import Stage4Consensus
from synapseflow.pipeline.stage5_synthesis import Stage5Synthesis
from synapseflow.models import SubTask

@pytest.fixture
def featherless():
    return FeatherlessClient()

@pytest.fixture
def wolfram():
    return WolframClient()

def test_stage1_decomposition(featherless):
    stage1 = Stage1Decomposition(featherless)
    prompt = "Model the battery heat loss at 40C and 15A with internal resistance 0.042 ohms."
    subtasks, trace = stage1.execute(prompt, domain="engineering")
    
    assert len(subtasks) >= 2
    assert trace.stage_number == 1
    assert trace.duration_ms > 0
    assert any(t.requires_symbolic_verification for t in subtasks)

def test_stage2_reasoning(featherless):
    stage2 = Stage2Reasoning(featherless)
    tasks = [
        SubTask(
            id="task_1",
            title="Formulate Equation",
            description="Derive Joule loss formula",
            assigned_model_role="reasoner",
            assigned_model_id=settings.MODELS["reasoner"],
            requires_symbolic_verification=True
        )
    ]
    results, trace = stage2.execute(tasks, "Test Context")
    assert len(results) == 1
    assert results[0].status == "completed"
    assert results[0].output is not None
    assert len(results[0].output) > 20

def test_stage3_wolfram_symbolic_verification(wolfram):
    stage3 = Stage3Verification(wolfram)
    
    # Valid equation: 225 * 0.042 = 9.45
    task_valid = SubTask(
        id="task_valid",
        title="Joule Loss",
        description="Math step",
        assigned_model_role="reasoner",
        assigned_model_id="test",
        requires_symbolic_verification=True,
        output="Joule loss calculation: 225 * 0.042 = 9.45 Watts."
    )
    
    claims, hallucination_detected, count, trace = stage3.execute([task_valid])
    assert len(claims) >= 1
    assert claims[0].is_valid is True
    assert hallucination_detected is False
    assert count == 0

def test_stage3_hallucination_flagging(wolfram):
    stage3 = Stage3Verification(wolfram)
    
    # Hallucinated equation: 225 * 0.042 = 14.8 (Mathematically False)
    task_hallucinated = SubTask(
        id="task_hallucinated",
        title="Bad Math",
        description="Math step",
        assigned_model_role="reasoner",
        assigned_model_id="test",
        requires_symbolic_verification=True,
        output="Joule loss is: 225 * 0.042 = 14.8 Watts."
    )
    
    claims, hallucination_detected, count, trace = stage3.execute([task_hallucinated])
    assert len(claims) >= 1
    assert claims[0].is_valid is False
    assert hallucination_detected is True
    assert count >= 1

def test_stage4_consensus(featherless):
    stage4 = Stage4Consensus(featherless)
    tasks = [
        SubTask(id="task_1", title="T1", description="D1", assigned_model_id="m1", output="Output 1")
    ]
    consensus, trace = stage4.execute(tasks, [], "Test Prompt")
    assert "consensus_reached" in consensus
    assert "confidence_score" in consensus
    assert consensus["confidence_score"] >= 0.80

def test_stage5_synthesis(featherless):
    stage5 = Stage5Synthesis(featherless)
    tasks = [
        SubTask(id="task_1", title="T1", description="D1", assigned_model_id="m1", output="Output 1")
    ]
    report, trace = stage5.execute("Test Prompt", "engineering", tasks, [], {"confidence_score": 0.99})
    assert len(report) > 50
    assert trace.stage_number == 5
