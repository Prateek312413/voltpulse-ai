"""
CockroachDB Memory Storage & Vector Retrieval Engine
Provides robust vector indexing, hybrid SQL querying, ACID transaction coordination,
and audit trail generation for the AegisMed agent swarm.
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from aegismed.database.models import (
    ClinicalEpisode, WorkingMemorySession, SemanticGuideline,
    ReflectiveInsight, AgentAuditLog, Patient
)
from aegismed.database.connection import active_backend
from aegismed.providers.gateway import gateway
from aegismed.config import settings

logger = logging.getLogger("aegismed.cockroach_store")


class CockroachMemoryStore:
    """Core memory engine interfacing with CockroachDB Distributed SQL & Vector Storage."""

    def __init__(self, db: Session):
        self.db = db
        self.backend = active_backend

    def log_audit(
        self,
        patient_uid: str,
        agent_name: str,
        action_type: str,
        memory_tier: str,
        query_payload: Dict[str, Any],
        result_summary: str,
        session_id: Optional[str] = None,
        duration_ms: float = 0.0
    ):
        """Records immutable audit trail of memory operations in CockroachDB."""
        try:
            log_entry = AgentAuditLog(
                session_id=session_id,
                patient_uid=patient_uid,
                agent_name=agent_name,
                action_type=action_type,
                memory_tier=memory_tier,
                query_payload=query_payload,
                result_summary=result_summary,
                execution_time_ms=duration_ms
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            self.db.rollback()

    def vector_search_episodes(
        self,
        patient_uid: str,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.50
    ) -> List[Tuple[ClinicalEpisode, float]]:
        """
        Executes semantic vector similarity search over patient's longitudinal clinical episodes.
        Utilizes CockroachDB vector indexing or cosine ranking.
        """
        start_time = time.time()
        query_embedding = gateway.get_embedding(query_text)
        
        episodes = self.db.query(ClinicalEpisode).filter(
            ClinicalEpisode.patient_uid == patient_uid
        ).all()

        scored_episodes = []
        for ep in episodes:
            if ep.embedding:
                sim = gateway.compute_cosine_similarity(query_embedding, ep.embedding)
                if sim >= threshold:
                    scored_episodes.append((ep, sim))
            else:
                # Text fallback match
                if any(word in ep.chief_complaint.lower() for word in query_text.lower().split()):
                    scored_episodes.append((ep, 0.60))

        # Sort descending by similarity score
        scored_episodes.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_episodes[:top_k]

        duration = (time.time() - start_time) * 1000.0
        self.log_audit(
            patient_uid=patient_uid,
            agent_name="CockroachMemoryStore",
            action_type="EPISODIC_VECTOR_SEARCH",
            memory_tier="EPISODIC",
            query_payload={"query_text": query_text, "top_k": top_k, "threshold": threshold},
            result_summary=f"Retrieved {len(top_results)} historical episodes in {duration:.2f}ms",
            duration_ms=duration
        )
        return top_results

    def search_semantic_guidelines(
        self,
        query_text: str,
        entities: List[str] = None,
        top_k: int = 5
    ) -> List[Tuple[SemanticGuideline, float]]:
        """
        Hybrid search combining SQL keyword/entity filters with vector cosine distance
        across clinical guidelines and contraindication rules in CockroachDB.
        """
        start_time = time.time()
        query_embedding = gateway.get_embedding(query_text)
        
        query = self.db.query(SemanticGuideline)
        guidelines = query.all()

        scored_guidelines = []
        entities_lower = [e.lower() for e in (entities or [])]

        for g in guidelines:
            sim = 0.0
            if g.embedding:
                sim = gateway.compute_cosine_similarity(query_embedding, g.embedding)
            
            # Boost score if specific entity matches
            entity_match = False
            if entities_lower:
                if (g.entity_a and g.entity_a.lower() in entities_lower) or \
                   (g.entity_b and g.entity_b.lower() in entities_lower):
                    sim = max(sim, 0.85) + 0.15
                    entity_match = True

            if sim >= 0.50 or entity_match:
                scored_guidelines.append((g, min(sim, 1.0)))

        scored_guidelines.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_guidelines[:top_k]

        duration = (time.time() - start_time) * 1000.0
        return top_results
