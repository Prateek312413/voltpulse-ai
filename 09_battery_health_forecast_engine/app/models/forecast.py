"""
Forecast Database Model.
Stores versioned SOH predictions with full uncertainty intervals and model configurations.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(128), primary_key=True, index=True)
    battery_id = Column(String(64), ForeignKey("batteries.id"), nullable=False, index=True)
    forecast_version = Column(Integer, nullable=False, default=1, index=True)
    source_telemetry_version = Column(Integer, nullable=False, index=True)
    target_cycle = Column(Integer, nullable=False, index=True)
    
    predicted_soh = Column(Float, nullable=False)
    std_dev = Column(Float, nullable=False)
    lower_ci = Column(Float, nullable=False)
    upper_ci = Column(Float, nullable=False)
    
    selected_kernel = Column(String(64), nullable=False)
    hyperparameters_json = Column(Text, nullable=True)
    jitter_used = Column(Float, nullable=False, default=0.0)
    noise_variance = Column(Float, nullable=False, default=1e-4)
    multi_horizon_json = Column(Text, nullable=True)  # Detailed curve points
    
    previous_forecast_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    battery = relationship("Battery", back_populates="forecasts")

    def to_dict(self):
        params = json.loads(self.hyperparameters_json) if self.hyperparameters_json else {}
        horizon = json.loads(self.multi_horizon_json) if self.multi_horizon_json else []
        return {
            "forecast_id": self.id,
            "battery_id": self.battery_id,
            "forecast_version": self.forecast_version,
            "source_telemetry_version": self.source_telemetry_version,
            "target_cycle": self.target_cycle,
            "predicted_soh": round(self.predicted_soh, 4),
            "std_dev": round(self.std_dev, 4),
            "lower_ci": round(self.lower_ci, 4),
            "upper_ci": round(self.upper_ci, 4),
            "selected_kernel": self.selected_kernel,
            "hyperparameters": params,
            "jitter_used": self.jitter_used,
            "noise_variance": self.noise_variance,
            "previous_forecast_id": self.previous_forecast_id,
            "multi_horizon_points": horizon,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
