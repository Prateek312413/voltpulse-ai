"""
Forecast Diff Database Model.
Stores audit diffs comparing forecast versions before and after reconciliation.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ForecastDiff(Base):
    __tablename__ = "forecast_diffs"

    id = Column(String(128), primary_key=True, index=True)
    battery_id = Column(String(64), ForeignKey("batteries.id"), nullable=False, index=True)
    target_cycle = Column(Integer, nullable=False, index=True)
    
    old_forecast_id = Column(String(128), nullable=True)
    old_forecast_version = Column(Integer, nullable=False, default=1)
    new_forecast_id = Column(String(128), nullable=False)
    new_forecast_version = Column(Integer, nullable=False, default=2)
    
    old_soh = Column(Float, nullable=False)
    new_soh = Column(Float, nullable=False)
    delta_soh = Column(Float, nullable=False)
    
    old_std = Column(Float, nullable=False)
    new_std = Column(Float, nullable=False)
    delta_std = Column(Float, nullable=False)
    
    old_kernel = Column(String(64), nullable=False)
    new_kernel = Column(String(64), nullable=False)
    kernel_changed = Column(Boolean, nullable=False, default=False)
    
    triggering_observation_ids_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    battery = relationship("Battery", back_populates="diffs")

    def to_dict(self):
        cause_ids = json.loads(self.triggering_observation_ids_json) if self.triggering_observation_ids_json else []
        return {
            "id": self.id,
            "battery_id": self.battery_id,
            "target_cycle": self.target_cycle,
            "old_forecast_id": self.old_forecast_id,
            "old_forecast_version": self.old_forecast_version,
            "new_forecast_id": self.new_forecast_id,
            "new_forecast_version": self.new_forecast_version,
            "old_soh": round(self.old_soh, 4),
            "new_soh": round(self.new_soh, 4),
            "delta_soh": round(self.delta_soh, 4),
            "old_std": round(self.old_std, 4),
            "new_std": round(self.new_std, 4),
            "delta_std": round(self.delta_std, 4),
            "old_kernel": self.old_kernel,
            "new_kernel": self.new_kernel,
            "kernel_changed": self.kernel_changed,
            "triggering_observation_ids": cause_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
