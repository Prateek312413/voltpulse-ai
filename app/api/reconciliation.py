"""
Reconciliation, Diff Audit, Time-Travel, and Replay Verification API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.database import get_db
from app.models.battery import Battery
from app.models.telemetry import TelemetryObservation
from app.models.forecast import Forecast
from app.models.diff import ForecastDiff
from app.schemas.diff import ForecastDiffResponse
from app.core.reconciler import reconcile_single_forecast
from app.core.replay import replay_telemetry_version, verify_determinism_replay

router = APIRouter(prefix="/batteries/{battery_id}", tags=["Reconciliation & Audit"])


@router.post("/reconcile", response_model=List[ForecastDiffResponse])
def trigger_reconciliation(battery_id: str, db: Session = Depends(get_db)):
    """
    Explicitly forces reconciliation of all existing forecasts against the active telemetry dataset.
    Generates new forecast versions and logs semantic diffs.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    existing_forecasts = db.query(Forecast).filter(Forecast.battery_id == battery_id).all()
    if not existing_forecasts:
        return []

    target_cycles = sorted(list(set(fc.target_cycle for fc in existing_forecasts)))
    all_obs = [o.to_dict() for o in db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == battery_id).all()]
    
    diff_results = []
    for tc in target_cycles:
        latest_fc = (
            db.query(Forecast)
            .filter(Forecast.battery_id == battery_id, Forecast.target_cycle == tc)
            .order_by(Forecast.forecast_version.desc())
            .first()
        )
        
        new_fc_res, diff_res = reconcile_single_forecast(
            battery_id=battery_id,
            target_cycle=tc,
            latest_old_forecast=latest_fc.to_dict() if latest_fc else None,
            all_observations=all_obs,
            new_telemetry_version=battery.active_telemetry_version,
            triggering_observation_ids=["MANUAL_RECONCILIATION"]
        )

        new_fc_id = f"FC-{battery.id}-C{tc}-v{new_fc_res.forecast_version}"
        db_fc = Forecast(
            id=new_fc_id,
            battery_id=battery.id,
            forecast_version=new_fc_res.forecast_version,
            source_telemetry_version=battery.active_telemetry_version,
            target_cycle=tc,
            predicted_soh=new_fc_res.predicted_soh,
            std_dev=new_fc_res.std_dev,
            lower_ci=new_fc_res.lower_ci,
            upper_ci=new_fc_res.upper_ci,
            selected_kernel=new_fc_res.selected_kernel,
            hyperparameters_json=json.dumps(new_fc_res.hyperparameters),
            jitter_used=new_fc_res.jitter_used,
            noise_variance=new_fc_res.noise_variance,
            previous_forecast_id=latest_fc.id if latest_fc else None,
            multi_horizon_json=json.dumps(new_fc_res.multi_horizon_points)
        )
        db.add(db_fc)

        if diff_res:
            diff_id = f"DIFF-{battery.id}-C{tc}-v{diff_res.old_forecast_version}-to-v{diff_res.new_forecast_version}"
            db_diff = ForecastDiff(
                id=diff_id,
                battery_id=battery.id,
                target_cycle=tc,
                old_forecast_id=diff_res.old_forecast_id,
                old_forecast_version=diff_res.old_forecast_version,
                new_forecast_id=new_fc_id,
                new_forecast_version=diff_res.new_forecast_version,
                old_soh=diff_res.old_soh,
                new_soh=diff_res.new_soh,
                delta_soh=diff_res.delta_soh,
                old_std=diff_res.old_std,
                new_std=diff_res.new_std,
                delta_std=diff_res.delta_std,
                old_kernel=diff_res.old_kernel,
                new_kernel=diff_res.new_kernel,
                kernel_changed=diff_res.kernel_changed,
                triggering_observation_ids_json=json.dumps(diff_res.triggering_observation_ids)
            )
            db.add(db_diff)
            diff_results.append(db_diff)

    db.commit()
    for d in diff_results:
        db.refresh(d)

    return [d.to_dict() for d in diff_results]


@router.get("/forecast-diffs", response_model=List[ForecastDiffResponse])
def get_forecast_diffs(
    battery_id: str,
    target_cycle: Optional[int] = Query(None, description="Filter diffs by target cycle"),
    db: Session = Depends(get_db)
):
    """Retrieves all semantic forecast diffs and audit logs generated for the battery."""
    query = db.query(ForecastDiff).filter(ForecastDiff.battery_id == battery_id)
    if target_cycle:
        query = query.filter(ForecastDiff.target_cycle == target_cycle)

    query = query.order_by(ForecastDiff.created_at.desc())
    return [d.to_dict() for d in query.all()]


@router.get("/time-travel")
def time_travel_forecast(
    battery_id: str,
    telemetry_version: int = Query(..., ge=1, description="Historical telemetry version to reconstruct"),
    target_cycle: int = Query(..., ge=1, description="Target forecast cycle"),
    db: Session = Depends(get_db)
):
    """
    Historical Time-Travel: reconstructs the exact active dataset and GPR forecast
    as it existed at historical telemetry_version.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    all_obs = [o.to_dict() for o in db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == battery_id).all()]
    
    try:
        forecast_res, metadata = replay_telemetry_version(
            all_observations=all_obs,
            target_telemetry_version=telemetry_version,
            target_cycle=target_cycle
        )
        return {
            "battery_id": battery_id,
            "replayed_telemetry_version": telemetry_version,
            "target_cycle": target_cycle,
            "forecast": forecast_res.to_dict(),
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/replay")
def verify_replay_determinism(
    battery_id: str,
    target_cycle: int = Query(..., ge=1),
    kernel_name: str = Query("RBF"),
    runs: int = Query(3, ge=2, le=10),
    db: Session = Depends(get_db)
):
    """Runs multiple independent evaluations and verifies bit-for-bit identical outputs."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    obs = [o.to_dict() for o in db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == battery_id, TelemetryObservation.is_active == True).all()]
    if len(obs) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Need at least 3 observations for replay.")

    res = verify_determinism_replay(obs, target_cycle=target_cycle, kernel_name=kernel_name, num_runs=runs)
    return res
