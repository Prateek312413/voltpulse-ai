"""
Configuration settings for the Uncertainty-Aware Battery Health Forecast Engine.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Uncertainty-Aware Battery Health Forecast Engine"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./battery_forecast_engine.db"
    
    # Validation Rules
    SOH_MIN: float = 0.0
    SOH_MAX: float = 1.2
    VOLTAGE_MIN: float = 2.0
    VOLTAGE_MAX: float = 5.0
    TEMPERATURE_MIN: float = -30.0  # Celsius
    TEMPERATURE_MAX: float = 85.0   # Celsius
    CURRENT_MIN: float = -10.0      # Amperes (charging / discharging)
    CURRENT_MAX: float = 10.0
    
    # Gaussian Process Numerical Stability Configuration
    # PRD Requirement: bounded deterministic jitter sequence ladder
    JITTER_SEQUENCE: List[float] = [0.0, 1e-10, 1e-8, 1e-6, 1e-4]
    
    # Prediction & Confidence Interval Configuration
    CONFIDENCE_LEVEL: float = 0.95
    CI_Z_SCORE: float = 1.959963984540054  # 95% two-tailed normal Z
    
    # Validation Split
    TRAIN_SPLIT_RATIO: float = 0.75  # 75% temporal train, 25% holdout validation

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
