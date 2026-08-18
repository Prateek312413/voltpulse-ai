"""
SynapseFlow Configuration
Handles environment settings, API keys, Featherless models, and Wolfram endpoints.
"""

import os
from typing import Dict, Any

class Settings:
    # Service Information
    APP_NAME: str = "SynapseFlow Orchestrator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENV", "development")
    
    # Featherless.ai Settings
    FEATHERLESS_API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "")
    FEATHERLESS_BASE_URL: str = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
    
    # Model Router Definitions (Open-Source Models on Featherless)
    MODELS: Dict[str, str] = {
        "router": "mistralai/Mistral-Nemo-Instruct-2407",           # Fast intent & decomposition
        "reasoner": "deepseek-ai/DeepSeek-V3-0324",                 # Deep mathematical & logical reasoning
        "coder": "Qwen/Qwen2.5-Coder-32B-Instruct",                 # Code generation & structured output
        "consensus": "moonshotai/Kimi-K2.5",                        # Multi-perspective synthesis & consensus
        "synthesizer": "deepseek-ai/DeepSeek-V3-0324"               # Final verified report generation
    }
    
    # Wolfram Settings
    WOLFRAM_APP_ID: str = os.getenv("WOLFRAM_APP_ID", "")
    WOLFRAM_API_URL: str = os.getenv("WOLFRAM_API_URL", "https://api.wolframalpha.com/v2/query")
    
    # Execution & Safety Limits
    MAX_SUBTASKS: int = 5
    VERIFICATION_TIMEOUT_SECONDS: float = 10.0
    TEMPERATURE_ROUTER: float = 0.2
    TEMPERATURE_REASONER: float = 0.4
    TEMPERATURE_SYNTHESIZER: float = 0.1
    
    # Simulation / Offline Fallback Mode
    # If no API key is provided, the engine runs in deterministic high-fidelity simulation mode
    ALLOW_MOCK_FALLBACK: bool = True

settings = Settings()
