"""
Telemetry Observation Database Model.
Supports versioning, correction lineages, and dual timestamps (recorded_at vs received_at).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class TelemetryObservation(Base):
    __tablename__ = "telemetry_observations"

    # Unique synthetic PK or observation_id
    id = Column(String(128), primary_key=True, index=True)
    observation_id = Column(String(64), nullable=False, index=True)  # User-supplied ID
    battery_id = Column(String(64), ForeignKey("batteries.id"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False, index=True)
    
    recorded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)  # Event Time
    received_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)  # Receive Time
    
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    capacity = Column(Float, nullable=True)
    soh = Column(Float, nullable=False)
    
    # Versioning & Lineage
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    replaces_id = Column(String(128), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    telemetry_version = Column(Integer, nullable=False, default=1, index=True)
    correction_reason = Column(Text, nullable=True)

    battery = relationship("Battery", back_populates="observations")

    def to_dict(self):
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "battery_id": self.battery_id,
            "cycle_number": self.cycle_number,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "voltage": self.voltage,
            "current": self.current,
            "temperature": self.temperature,
            "capacity": self.capacity,
            "soh": round(self.soh, 4) if self.soh is not None else None,
            "is_active": self.is_active,
            "replaces_id": self.replaces_id,
            "version": self.version,
            "telemetry_version": self.telemetry_version,
            "correction_reason": self.correction_reason
        }
