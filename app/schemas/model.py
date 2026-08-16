"""
Pydantic Schemas for Model Evaluation and Selection.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ModelEvaluateRequest(BaseModel):
    telemetry_version: Optional[int] = Field(None, description="Optional target telemetry version to evaluate against")
    target_coverage: float = Field(default=0.95, gt=0.0, lt=1.0, description="Target prediction-interval coverage")
    include_baselines: bool = Field(default=True, description="Whether to include Polynomial/KNN/DecisionTree baselines")


class ModelEvaluationItem(BaseModel):
    id: Optional[str] = None
    kernel_name: str
    model_name: str
    status: str
    rmse: Optional[float] = None
    mae: Optional[float] = None
    coverage: Optional[float] = None
    coverage_error: Optional[float] = None
    log_marginal_likelihood: Optional[float] = None
    jitter_used: float
    hyperparameters: Dict[str, float]
    is_selected: bool
    selection_rank: int
    error_message: Optional[str] = None
    elapsed_seconds: Optional[float] = None


class ModelEvaluationResponse(BaseModel):
    battery_id: str
    telemetry_version: int
    selected_model: ModelEvaluationItem
    all_candidates: List[ModelEvaluationItem]
