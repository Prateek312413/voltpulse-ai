"""
Model Evaluation Database Model.
Stores evaluation metrics and diagnostic parameters across candidate kernels.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(String(64), primary_key=True, index=True)
    battery_id = Column(String(64), ForeignKey("batteries.id"), nullable=False, index=True)
    telemetry_version = Column(Integer, nullable=False, index=True)
    kernel_name = Column(String(64), nullable=False)
    model_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)  # "SUCCESS" or "FAILED"
    
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    coverage = Column(Float, nullable=True)
    coverage_error = Column(Float, nullable=True)
    log_marginal_likelihood = Column(Float, nullable=True)
    jitter_used = Column(Float, nullable=False, default=0.0)
    hyperparameters_json = Column(Text, nullable=True)
    is_selected = Column(Boolean, nullable=False, default=False)
    selection_rank = Column(Integer, nullable=False, default=999)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    battery = relationship("Battery", back_populates="evaluations")

    def to_dict(self):
        params = json.loads(self.hyperparameters_json) if self.hyperparameters_json else {}
        return {
            "id": self.id,
            "battery_id": self.battery_id,
            "telemetry_version": self.telemetry_version,
            "kernel_name": self.kernel_name,
            "model_name": self.model_name,
            "status": self.status,
            "rmse": round(self.rmse, 6) if self.rmse is not None else None,
            "mae": round(self.mae, 6) if self.mae is not None else None,
            "coverage": round(self.coverage, 4) if self.coverage is not None else None,
            "coverage_error": round(self.coverage_error, 4) if self.coverage_error is not None else None,
            "log_marginal_likelihood": round(self.log_marginal_likelihood, 4) if self.log_marginal_likelihood is not None else None,
            "jitter_used": self.jitter_used,
            "hyperparameters": params,
            "is_selected": self.is_selected,
            "selection_rank": self.selection_rank,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
