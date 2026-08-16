"""
Audit Log Database Model.
Logs all telemetry ingestion, corrections, evaluations, and reconciliation events.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    battery_id = Column(String(64), ForeignKey("batteries.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    battery = relationship("Battery", back_populates="audit_logs")

    def to_dict(self):
        details = json.loads(self.details_json) if self.details_json else {}
        return {
            "id": self.id,
            "battery_id": self.battery_id,
            "event_type": self.event_type,
            "details": details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
