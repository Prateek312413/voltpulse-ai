"""
Telemetry Ingestion, Correction, and Query API Endpoints.
"""

from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.battery import Battery
from app.models.telemetry import TelemetryObservation
from app.models.forecast import Forecast
from app.models.diff import ForecastDiff
from app.models.audit import AuditLog
from app.schemas.telemetry import (
    TelemetryCreate,
    TelemetryCorrect,
    TelemetryResponse,
    TelemetryBatchCreate
)
from app.core.validation import validate_telemetry_payload, check_payload_equivalence, ValidationError, ConflictError
from app.core.reconciler import reconcile_single_forecast

router = APIRouter(prefix="/batteries/{battery_id}/observations", tags=["Telemetry"])


def _run_reconciliation_if_needed(db: Session, battery: Battery, triggering_obs_ids: List[str]):
    """Checks existing forecasts and automatically reconciles them when telemetry changes."""
    existing_forecasts = db.query(Forecast).filter(Forecast.battery_id == battery.id).all()
    if not existing_forecasts:
        return

    # Find unique target cycles from existing forecasts
    target_cycles = sorted(list(set(fc.target_cycle for fc in existing_forecasts)))
    all_obs = [o.to_dict() for o in db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == battery.id).all()]

    for tc in target_cycles:
        latest_fc = (
            db.query(Forecast)
            .filter(Forecast.battery_id == battery.id, Forecast.target_cycle == tc)
            .order_by(Forecast.forecast_version.desc())
            .first()
        )
        new_fc_res, diff_res = reconcile_single_forecast(
            battery_id=battery.id,
            target_cycle=tc,
            latest_old_forecast=latest_fc.to_dict() if latest_fc else None,
            all_observations=all_obs,
            new_telemetry_version=battery.active_telemetry_version,
            triggering_observation_ids=triggering_obs_ids
        )

        # Persist new forecast version
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

        # Persist diff
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

    db.commit()


@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def ingest_observation(battery_id: str, payload: TelemetryCreate, db: Session = Depends(get_db)):
    """Ingests a single telemetry observation, validates payload, and tracks versioning."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    obs_dict = payload.dict()
    obs_dict["battery_id"] = battery_id

    # 1. Validation
    try:
        validate_telemetry_payload(obs_dict)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ve.message)

    # 2. Duplicate & Conflict Detection
    existing_active = (
        db.query(TelemetryObservation)
        .filter(
            TelemetryObservation.battery_id == battery_id,
            TelemetryObservation.observation_id == payload.observation_id,
            TelemetryObservation.is_active == True
        )
        .first()
    )

    if existing_active:
        if check_payload_equivalence(existing_active.to_dict(), obs_dict):
            # Idempotent re-submission: return existing record
            return existing_active.to_dict()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Observation ID '{payload.observation_id}' already exists with different payload. "
                    f"Use POST /batteries/{battery_id}/observations/{payload.observation_id}/correct to submit a correction."
                )
            )

    # 3. Timestamps
    receive_time = datetime.now(timezone.utc)
    if payload.recorded_at:
        try:
            event_time = datetime.fromisoformat(payload.recorded_at.replace("Z", "+00:00"))
        except ValueError:
            event_time = receive_time
    else:
        event_time = receive_time

    # Increment telemetry version
    battery.active_telemetry_version += 1

    # Record ID format
    internal_id = f"OBS-{battery_id}-{payload.observation_id}-v1"

    new_obs = TelemetryObservation(
        id=internal_id,
        observation_id=payload.observation_id,
        battery_id=battery_id,
        cycle_number=payload.cycle_number,
        recorded_at=event_time,
        received_at=receive_time,
        voltage=payload.voltage,
        current=payload.current,
        temperature=payload.temperature,
        capacity=payload.capacity,
        soh=payload.soh,
        is_active=True,
        version=1,
        telemetry_version=battery.active_telemetry_version
    )
    db.add(new_obs)

    # Audit log
    audit = AuditLog(
        battery_id=battery_id,
        event_type="OBSERVATION_INGESTED",
        details_json=json.dumps(obs_dict)
    )
    db.add(audit)
    db.commit()
    db.refresh(new_obs)

    # 4. Trigger reconciliation if historical forecasts exist
    _run_reconciliation_if_needed(db, battery, [payload.observation_id])

    return new_obs.to_dict()


@router.post("/batch", response_model=List[TelemetryResponse], status_code=status.HTTP_201_CREATED)
def ingest_batch_observations(battery_id: str, payload: TelemetryBatchCreate, db: Session = Depends(get_db)):
    """Ingests a batch of telemetry observations atomically."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    results = []
    triggering_ids = []
    receive_time = datetime.now(timezone.utc)

    for item in payload.observations:
        obs_dict = item.dict()
        obs_dict["battery_id"] = battery_id
        try:
            validate_telemetry_payload(obs_dict)
        except ValidationError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Error in {item.observation_id}: {ve.message}")

        existing = (
            db.query(TelemetryObservation)
            .filter(
                TelemetryObservation.battery_id == battery_id,
                TelemetryObservation.observation_id == item.observation_id,
                TelemetryObservation.is_active == True
            )
            .first()
        )
        if existing:
            if check_payload_equivalence(existing.to_dict(), obs_dict):
                results.append(existing.to_dict())
                continue
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Conflict on observation {item.observation_id}. Different payload already exists."
                )

        if item.recorded_at:
            try:
                event_time = datetime.fromisoformat(item.recorded_at.replace("Z", "+00:00"))
            except ValueError:
                event_time = receive_time
        else:
            event_time = receive_time

        battery.active_telemetry_version += 1
        internal_id = f"OBS-{battery_id}-{item.observation_id}-v1"

        new_obs = TelemetryObservation(
            id=internal_id,
            observation_id=item.observation_id,
            battery_id=battery_id,
            cycle_number=item.cycle_number,
            recorded_at=event_time,
            received_at=receive_time,
            voltage=item.voltage,
            current=item.current,
            temperature=item.temperature,
            capacity=item.capacity,
            soh=item.soh,
            is_active=True,
            version=1,
            telemetry_version=battery.active_telemetry_version
        )
        db.add(new_obs)
        results.append(new_obs)
        triggering_ids.append(item.observation_id)

    db.commit()
    for r in results:
        if isinstance(r, TelemetryObservation):
            db.refresh(r)

    _run_reconciliation_if_needed(db, battery, triggering_ids)

    return [r.to_dict() if isinstance(r, TelemetryObservation) else r for r in results]


@router.post("/{observation_id}/correct", response_model=TelemetryResponse)
def correct_observation(
    battery_id: str,
    observation_id: str,
    payload: TelemetryCorrect,
    db: Session = Depends(get_db)):
    """
    Submits a corrected observation value.
    Preserves historical observation in audit history, deactivates it,
    creates new active observation version, and triggers forecast reconciliation.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Battery '{battery_id}' not found.")

    existing = (
        db.query(TelemetryObservation)
        .filter(
            TelemetryObservation.battery_id == battery_id,
            TelemetryObservation.observation_id == observation_id,
            TelemetryObservation.is_active == True
        )
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active observation with ID '{observation_id}' not found for battery '{battery_id}'."
        )

    # Validate new payload
    corr_dict = {
        "observation_id": observation_id,
        "battery_id": battery_id,
        "cycle_number": existing.cycle_number,
        "soh": payload.soh,
        "voltage": payload.voltage if payload.voltage is not None else existing.voltage,
        "current": payload.current if payload.current is not None else existing.current,
        "temperature": payload.temperature if payload.temperature is not None else existing.temperature,
        "capacity": payload.capacity if payload.capacity is not None else existing.capacity,
        "recorded_at": existing.recorded_at.isoformat()
    }
    try:
        validate_telemetry_payload(corr_dict)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ve.message)

    # 1. Supersede previous active observation
    existing.is_active = False

    # 2. Increment versions
    new_version_num = existing.version + 1
    battery.active_telemetry_version += 1
    new_internal_id = f"OBS-{battery_id}-{observation_id}-v{new_version_num}"

    # 3. Create new corrected observation
    corrected_obs = TelemetryObservation(
        id=new_internal_id,
        observation_id=observation_id,
        battery_id=battery_id,
        cycle_number=existing.cycle_number,
        recorded_at=existing.recorded_at,
        received_at=datetime.now(timezone.utc),
        voltage=corr_dict["voltage"],
        current=corr_dict["current"],
        temperature=corr_dict["temperature"],
        capacity=corr_dict["capacity"],
        soh=corr_dict["soh"],
        is_active=True,
        replaces_id=existing.id,
        version=new_version_num,
        telemetry_version=battery.active_telemetry_version,
        correction_reason=payload.correction_reason
    )
    db.add(corrected_obs)

    # Audit log
    audit = AuditLog(
        battery_id=battery_id,
        event_type="OBSERVATION_CORRECTED",
        details_json=json.dumps({
            "observation_id": observation_id,
            "previous_internal_id": existing.id,
            "previous_soh": existing.soh,
            "new_soh": payload.soh,
            "correction_reason": payload.correction_reason
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(corrected_obs)

    # 4. Trigger reconciliation
    _run_reconciliation_if_needed(db, battery, [observation_id])

    return corrected_obs.to_dict()


@router.get("", response_model=List[TelemetryResponse])
def get_observations(
    battery_id: str,
    order_by: str = Query("event_time", enum=["event_time", "receive_time"], description="Sort timeline order"),
    active_only: bool = Query(True, description="Filter only currently active observations"),
    db: Session = Depends(get_db)
):
    """
    Retrieves telemetry observations for a battery in either event-time order or receive-time order.
    Demonstrates late-telemetry arrival decoupling from physical observation sequence.
    """
    query = db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == battery_id)
    
    if active_only:
        query = query.filter(TelemetryObservation.is_active == True)

    if order_by == "event_time":
        query = query.order_by(TelemetryObservation.cycle_number.asc(), TelemetryObservation.recorded_at.asc(), TelemetryObservation.id.asc())
    else:  # receive_time
        query = query.order_by(TelemetryObservation.received_at.asc(), TelemetryObservation.id.asc())

    records = query.all()
    return [r.to_dict() for r in records]
