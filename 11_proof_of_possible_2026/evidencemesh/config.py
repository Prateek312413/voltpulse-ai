"""
Configuration settings for EvidenceMesh.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "EvidenceMesh"
    TAGLINE: str = "Autonomous Causal Verification & Cryptographic Proof Engine"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Bayesian calibration settings
    DEFAULT_PRIOR_ALPHA: float = 2.0
    DEFAULT_PRIOR_BETA: float = 2.0
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    UNCERTAINTY_TOLERANCE_SIGMA: float = 0.15
    ECE_BIN_COUNT: int = 10

    # Merkle Proof settings
    MERKLE_HASH_ALGO: str = "sha256"
    CRYPTO_DOMAIN: str = "evidencemesh.proof-of-possible.2026"


settings = Settings()
