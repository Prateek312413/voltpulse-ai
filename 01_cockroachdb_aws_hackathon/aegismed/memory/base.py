"""
AegisMed Memory Base Schemas and Types
Defines the 4-Tier Memory Taxonomy, Graph Representation, and Query Interfaces.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime


class MemoryTier(str, Enum):
    WORKING = "WORKING"          # Tier 1: Active consultation state & transactional locks
    EPISODIC = "EPISODIC"        # Tier 2: Temporal patient encounters with vector embeddings
    SEMANTIC = "SEMANTIC"        # Tier 3: Medical knowledge, guidelines & contraindication rules
    REFLECTIVE = "REFLECTIVE"    # Tier 4: Autonomous meta-insights & discrepancy synthesis


class MemoryNode(BaseModel):
    """Represents a node in the interactive Agentic Memory Graph."""
    id: str
    label: str
    tier: MemoryTier
    timestamp: Optional[str] = None
    similarity_score: Optional[float] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: str


class MemoryEdge(BaseModel):
    """Represents a relationship or causal link between memories."""
    source: str
    target: str
    relationship: str # e.g. "CONTRAINDICATES", "TEMPORAL_PRECEDENCE", "HYPOTHESIZES", "EVIDENCED_BY"
    weight: float = 1.0


class MemoryGraph(BaseModel):
    """Complete visualizable memory graph for clinician UI."""
    patient_uid: str
    session_id: Optional[str] = None
    nodes: List[MemoryNode] = Field(default_factory=list)
    edges: List[MemoryEdge] = Field(default_factory=list)
    active_memory_count: int = 0


class MemoryRecallResult(BaseModel):
    """Standardized recall payload returned across all memory tiers."""
    tier: MemoryTier
    items: List[Dict[str, Any]]
    total_retrieved: int
    query_text: str
    execution_time_ms: float
    relevance_scores: List[float] = Field(default_factory=list)
