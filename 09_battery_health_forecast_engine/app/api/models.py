"""
Model Evaluation and Selection API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app.models.battery import Battery
from app.models.telemetry import TelemetryObservation
from app.models.evaluation import ModelEvaluation
from app.schemas.model import ModelEvaluateRequest, ModelEvaluationResponse, ModelEvaluationItem
from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models

router = APIRouter(prefix="/batteries/{battery_id}/models", tags=["Model Evaluation"])


@router.post("/evaluate", response_model=ModelEvaluationResponse)
def evaluate_models(battery_id: str, payload: ModelEvaluateRequest = ModelEvaluateRequest(), db: Session = Depends(get_db)):
    """
    Evaluates candidate GPR kernels and baselines using deterministic temporal splits.
    Selects the optimal model using the PRD deterministic hierarchy.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    # Fetch active observations
    obs_query = db.query(TelemetryObservation).filter(
        TelemetryObservation.battery_id == battery_id,
        TelemetryObservation.is_active == True
    )
    if payload.telemetry_version:
        obs_query = obs_query.filter(TelemetryObservation.telemetry_version <= payload.telemetry_version)

    obs_records = [o.to_dict() for o in obs_query.all()]
    if len(obs_records) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Battery has only {len(obs_records)} observations. At least 4 observations are required for temporal evaluation."
        )

    # Build active dataset
    _, pipeline_config, X, y = build_active_temporal_dataset(obs_records)

    # Evaluate
    summaries, best_model = evaluate_candidate_models(
        X=X,
        y=y,
        target_coverage=payload.target_coverage,
        include_baselines=payload.include_baselines
    )

    # Clear older evaluations for this telemetry version and persist new ones
    current_tel_ver = payload.telemetry_version or battery.active_telemetry_version
    db.query(ModelEvaluation).filter(
        ModelEvaluation.battery_id == battery_id,
        ModelEvaluation.telemetry_version == current_tel_ver
    ).delete()

    candidate_items = []
    for s in summaries:
        eval_id = f"EVAL-{battery_id}-v{current_tel_ver}-{s.kernel_type}"
        db_eval = ModelEvaluation(
            id=eval_id,
            battery_id=battery_id,
            telemetry_version=current_tel_ver,
            kernel_name=s.kernel_type,
            model_name=s.model_name,
            status=s.status,
            rmse=s.rmse,
            mae=s.mae,
            coverage=s.coverage,
            coverage_error=s.coverage_error,
            log_marginal_likelihood=s.log_marginal_likelihood,
            jitter_used=s.jitter_used,
            hyperparameters_json=json.dumps(s.hyperparameters),
            is_selected=s.is_selected,
            selection_rank=s.selection_rank,
            error_message=s.error_message,
            created_at=None
        )
        db.add(db_eval)
        candidate_items.append(ModelEvaluationItem(
            id=eval_id,
            kernel_name=s.kernel_type,
            model_name=s.model_name,
            status=s.status,
            rmse=s.rmse,
            mae=s.mae,
            coverage=s.coverage,
            coverage_error=s.coverage_error,
            log_marginal_likelihood=s.log_marginal_likelihood,
            jitter_used=s.jitter_used,
            hyperparameters=s.hyperparameters,
            is_selected=s.is_selected,
            selection_rank=s.selection_rank,
            error_message=s.error_message,
            elapsed_seconds=s.elapsed_seconds
        ))

    db.commit()

    selected_item = next(item for item in candidate_items if item.is_selected)

    return ModelEvaluationResponse(
        battery_id=battery_id,
        telemetry_version=current_tel_ver,
        selected_model=selected_item,
        all_candidates=candidate_items
    )


@router.get("", response_model=List[ModelEvaluationItem])
def get_latest_evaluations(battery_id: str, db: Session = Depends(get_db)):
    """Retrieves the latest model evaluation rankings for the battery."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    evals = (
        db.query(ModelEvaluation)
        .filter(ModelEvaluation.battery_id == battery_id)
        .order_by(ModelEvaluation.telemetry_version.desc(), ModelEvaluation.selection_rank.asc())
        .all()
    )
    return [
        ModelEvaluationItem(
            id=e.id,
            kernel_name=e.kernel_name,
            model_name=e.model_name,
            status=e.status,
            rmse=e.rmse,
            mae=e.mae,
            coverage=e.coverage,
            coverage_error=e.coverage_error,
            log_marginal_likelihood=e.log_marginal_likelihood,
            jitter_used=e.jitter_used,
            hyperparameters=json.loads(e.hyperparameters_json) if e.hyperparameters_json else {},
            is_selected=e.is_selected,
            selection_rank=e.selection_rank,
            error_message=e.error_message
        )
        for e in evals
    ]
