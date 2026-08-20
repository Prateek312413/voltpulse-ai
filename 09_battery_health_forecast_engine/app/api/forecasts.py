"""
Forecast Generation and Retrieval API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database import get_db
from app.models.battery import Battery
from app.models.telemetry import TelemetryObservation
from app.models.forecast import Forecast
from app.models.audit import AuditLog
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models
from app.core.forecaster import generate_forecast

router = APIRouter(prefix="/batteries/{battery_id}/forecasts", tags=["Forecasts"])


@router.post("", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(battery_id: str, payload: ForecastRequest, db: Session = Depends(get_db)):
    """Generates an uncertainty-aware SOH forecast for the requested future cycle."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    # Fetch active observations
    obs_query = db.query(TelemetryObservation).filter(
        TelemetryObservation.battery_id == battery_id,
        TelemetryObservation.is_active == True
    )
    obs_records = [o.to_dict() for o in obs_query.all()]
    if len(obs_records) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Battery has only {len(obs_records)} observations. At least 3 observations are required for GPR forecasting."
        )

    # Build active dataset
    _, pipeline_config, X, y = build_active_temporal_dataset(obs_records)

    # Select kernel
    if payload.kernel_name:
        selected_kernel = payload.kernel_name
        hyperparams = None
    else:
        summaries, best_model = evaluate_candidate_models(X, y)
        selected_kernel = best_model.kernel_type
        hyperparams = best_model.hyperparameters

    # Check previous forecast for version increment
    latest_fc = (
        db.query(Forecast)
        .filter(Forecast.battery_id == battery_id, Forecast.target_cycle == payload.target_cycle)
        .order_by(Forecast.forecast_version.desc())
        .first()
    )
    new_version = (latest_fc.forecast_version + 1) if latest_fc else 1

    # Run forecast
    fc_res = generate_forecast(
        X_train=X,
        y_train=y,
        pipeline_config=pipeline_config,
        target_cycle=payload.target_cycle,
        selected_kernel_name=selected_kernel,
        telemetry_version=battery.active_telemetry_version,
        forecast_version=new_version,
        hyperparameters=hyperparams,
        generate_curve_to_target=payload.generate_curve
    )

    fc_id = f"FC-{battery_id}-C{payload.target_cycle}-v{new_version}"
    db_fc = Forecast(
        id=fc_id,
        battery_id=battery_id,
        forecast_version=new_version,
        source_telemetry_version=battery.active_telemetry_version,
        target_cycle=payload.target_cycle,
        predicted_soh=fc_res.predicted_soh,
        std_dev=fc_res.std_dev,
        lower_ci=fc_res.lower_ci,
        upper_ci=fc_res.upper_ci,
        selected_kernel=fc_res.selected_kernel,
        hyperparameters_json=json.dumps(fc_res.hyperparameters),
        jitter_used=fc_res.jitter_used,
        noise_variance=fc_res.noise_variance,
        previous_forecast_id=latest_fc.id if latest_fc else None,
        multi_horizon_json=json.dumps(fc_res.multi_horizon_points)
    )
    db.add(db_fc)

    # Audit log
    audit = AuditLog(
        battery_id=battery_id,
        event_type="FORECAST_GENERATED",
        details_json=json.dumps({
            "forecast_id": fc_id,
            "version": new_version,
            "target_cycle": payload.target_cycle,
            "predicted_soh": fc_res.predicted_soh,
            "std_dev": fc_res.std_dev,
            "selected_kernel": fc_res.selected_kernel
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(db_fc)

    return db_fc.to_dict()


@router.get("", response_model=List[ForecastResponse])
def list_forecasts(
    battery_id: str,
    target_cycle: Optional[int] = Query(None, description="Filter by target cycle"),
    latest_only: bool = Query(False, description="Return only the latest version per target cycle"),
    db: Session = Depends(get_db)
):
    """Retrieves all versioned forecasts generated for the battery."""
    query = db.query(Forecast).filter(Forecast.battery_id == battery_id)
    if target_cycle:
        query = query.filter(Forecast.target_cycle == target_cycle)

    query = query.order_by(Forecast.target_cycle.asc(), Forecast.forecast_version.desc())
    records = query.all()

    if latest_only:
        seen_cycles = set()
        latest_records = []
        for r in records:
            if r.target_cycle not in seen_cycles:
                seen_cycles.add(r.target_cycle)
                latest_records.append(r)
        return [r.to_dict() for r in latest_records]

    return [r.to_dict() for r in records]


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast_by_id(battery_id: str, forecast_id: str, db: Session = Depends(get_db)):
    """Retrieves a specific forecast version by its unique ID."""
    fc = db.query(Forecast).filter(Forecast.battery_id == battery_id, Forecast.id == forecast_id).first()
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Forecast '{forecast_id}' not found.")
    return fc.to_dict()
