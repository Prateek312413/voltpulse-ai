"""
Battery Registry API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.battery import Battery
from app.models.audit import AuditLog
from app.schemas.battery import BatteryCreate, BatteryResponse
import json

router = APIRouter(prefix="/batteries", tags=["Batteries"])


@router.post("", response_model=BatteryResponse, status_code=status.HTTP_201_CREATED)
def create_battery(payload: BatteryCreate, db: Session = Depends(get_db)):
    """Registers a new battery into the forecast engine registry."""
    existing = db.query(Battery).filter(Battery.id == payload.battery_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Battery with ID '{payload.battery_id}' already exists."
        )

    battery = Battery(
        id=payload.battery_id,
        battery_type=payload.battery_type,
        nominal_capacity=payload.nominal_capacity,
        active_telemetry_version=1
    )
    db.add(battery)
    
    # Audit log
    audit = AuditLog(
        battery_id=battery.id,
        event_type="BATTERY_CREATED",
        details_json=json.dumps(payload.dict())
    )
    db.add(audit)
    db.commit()
    db.refresh(battery)
    return battery.to_dict()


@router.get("", response_model=List[BatteryResponse])
def list_batteries(db: Session = Depends(get_db)):
    """Retrieves all registered batteries."""
    batteries = db.query(Battery).all()
    return [b.to_dict() for b in batteries]


@router.get("/{battery_id}", response_model=BatteryResponse)
def get_battery(battery_id: str, db: Session = Depends(get_db)):
    """Retrieves battery metadata and active telemetry version."""
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery '{battery_id}' not found."
        )
    return battery.to_dict()
