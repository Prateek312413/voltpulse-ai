"""
AegisMed Configuration Module
Handles settings for CockroachDB, AWS Bedrock, Vector Dimensions, and Runtime Modes.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "AegisMed: Clinical Agentic Memory Engine"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CockroachDB Configuration
    # Supports CockroachDB Cloud Serverless / Dedicated connection strings
    # or PostgreSQL / Local SQLite fallback
    COCKROACH_DB_URL: str = os.getenv(
        "COCKROACH_DB_URL",
        "cockroachdb://root@localhost:26257/aegismed?sslmode=disable"
    )
    USE_FALLBACK_DB_IF_UNAVAILABLE: bool = True
    SQLITE_FALLBACK_PATH: str = "aegismed_memory.db"
    
    # Vector Configuration
    VECTOR_DIMENSION: int = 384  # Matches all-MiniLM-L6-v2 / Titan Embeddings
    SIMILARITY_THRESHOLD: float = 0.65
    TOP_K_EPISODIC_RECALL: int = 5
    
    # AWS Bedrock & Cloud Services
    AWS_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_SESSION_TOKEN: Optional[str] = os.getenv("AWS_SESSION_TOKEN", None)
    
    # Model IDs
    BEDROCK_LLM_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    
    # Simulation / Offline Evaluation Mode (guarantees 100% testability out of the box)
    OFFLINE_AI_MODE: bool = os.getenv("OFFLINE_AI_MODE", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
