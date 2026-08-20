"""
Battery Registry Database Model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class Battery(Base):
    __tablename__ = "batteries"

    id = Column(String(64), primary_key=True, index=True)
    battery_type = Column(String(64), nullable=False, default="Li-ion NMC")
    nominal_capacity = Column(Float, nullable=False, default=2.0)  # in Ah
    active_telemetry_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    observations = relationship("TelemetryObservation", back_populates="battery", cascade="all, delete-orphan")
    evaluations = relationship("ModelEvaluation", back_populates="battery", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="battery", cascade="all, delete-orphan")
    diffs = relationship("ForecastDiff", back_populates="battery", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="battery", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "battery_id": self.id,
            "battery_type": self.battery_type,
            "nominal_capacity": self.nominal_capacity,
            "active_telemetry_version": self.active_telemetry_version,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
