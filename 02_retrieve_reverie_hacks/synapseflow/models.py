"""
SynapseFlow Data Schemas & Pydantic Models
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SubTask(BaseModel):
    id: str = Field(..., description="Unique subtask identifier, e.g., 'task_1'")
    title: str = Field(..., description="Short title of the subtask")
    description: str = Field(..., description="Detailed instruction for the subtask")
    assigned_model_role: str = Field("reasoner", description="Assigned role: 'reasoner', 'coder', or 'router'")
    assigned_model_id: str = Field(..., description="Specific model ID from Featherless catalog")
    requires_symbolic_verification: bool = Field(False, description="Whether this task contains quantitative formulas to verify")
    status: str = Field("pending", description="'pending', 'running', 'completed', 'verified', 'failed'")
    output: Optional[str] = None
    reasoning_trace: Optional[List[str]] = Field(default_factory=list)

class QuantitativeClaim(BaseModel):
    claim_id: str
    expression: str = Field(..., description="Mathematical or statistical expression")
    claimed_value: Any = Field(..., description="Value asserted by the LLM")
    verified_value: Optional[Any] = None
    is_valid: Optional[bool] = None
    error_margin: Optional[float] = None
    verification_source: str = "Wolfram/SymPy Oracle"
    explanation: Optional[str] = None

class StageExecutionTrace(BaseModel):
    stage_number: int
    stage_name: str
    model_used: str
    duration_ms: float
    input_summary: str
    output_summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PipelineExecutionRequest(BaseModel):
    prompt: str = Field(..., description="Complex scientific, clinical, or engineering prompt")
    domain: Optional[str] = Field("general_scientific", description="'clinical', 'engineering', 'finance', 'physics', 'general_scientific'")
    human_in_the_loop_mode: bool = Field(False, description="Whether to pause before final synthesis for user override")
    strict_verification: bool = Field(True, description="Strictly reject mathematical hallucinations")

class PipelineExecutionResponse(BaseModel):
    pipeline_id: str
    timestamp: str
    input_prompt: str
    domain: str
    final_output: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    hallucination_detected: bool
    hallucination_count: int
    verified_claims: List[QuantitativeClaim] = Field(default_factory=list)
    subtasks: List[SubTask] = Field(default_factory=list)
    stage_traces: List[StageExecutionTrace] = Field(default_factory=list)
    total_latency_ms: float
    token_usage_estimate: int

class SinglePromptBaselineResult(BaseModel):
    model_name: str
    raw_response: str
    accuracy_score: float
    hallucination_rate: float
    latency_ms: float
    structural_validity: bool
    verified_math_error_count: int

class BenchmarkComparisonResult(BaseModel):
    test_case_id: str
    test_case_title: str
    domain: str
    input_prompt: str
    ground_truth_key_facts: List[str]
    single_prompt_baseline: SinglePromptBaselineResult
    synapseflow_workflow: PipelineExecutionResponse
    improvement_summary: Dict[str, Any]
