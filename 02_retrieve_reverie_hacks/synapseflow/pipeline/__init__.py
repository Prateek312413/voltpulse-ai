"""
SynapseFlow Pipeline Package
Coordinates the 5-stage deterministic multi-LLM prompt workflow.
"""
from .orchestrator import PipelineOrchestrator

__all__ = ["PipelineOrchestrator"]
