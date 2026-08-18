"""
Tier 2: Episodic Memory Manager
Maintains longitudinal patient encounter history, doctor transcripts, diagnostic labs,
and high-dimensional vector embeddings stored in CockroachDB.
"""

import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from aegismed.database.models import ClinicalEpisode
from aegismed.memory.cockroach_store import CockroachMemoryStore
from aegismed.providers.gateway import gateway

logger = logging.getLogger("aegismed.episodic_memory")


class EpisodicMemoryManager:
    """Manages patient's longitudinal episodic memory and vector recall."""

    def __init__(self, db: Session):
        self.db = db
        self.store = CockroachMemoryStore(db)

    def record_episode(
        self,
        patient_uid: str,
        chief_complaint: str,
        symptoms: List[str],
        diagnosis: str,
        prescribed_medications: List[Dict[str, Any]],
        vital_signs: Dict[str, Any] = None,
        physician_notes: str = "",
        lab_results: Dict[str, Any] = None,
        encounter_type: str = "OUTPATIENT_CONSULTATION",
        timestamp: Optional[datetime.datetime] = None,
        severity_score: float = 1.0
    ) -> ClinicalEpisode:
        """Stores a new clinical episode with precomputed vector embedding in CockroachDB."""
        episode_uid = f"ep_{uuid.uuid4().hex[:12]}"
        
        # Build comprehensive narrative text for vector embedding
        meds_text = ", ".join([f"{m.get('name', '')} {m.get('dose', '')}" for m in prescribed_medications])
        embedding_source_text = (
            f"Patient Encounter: {encounter_type}. "
            f"Chief Complaint: {chief_complaint}. "
            f"Symptoms: {', '.join(symptoms)}. "
            f"Diagnosis: {diagnosis}. "
            f"Medications Prescribed: {meds_text}. "
            f"Physician Notes: {physician_notes}. "
            f"Lab Values: {lab_results}"
        )
        
        embedding_vec = gateway.get_embedding(embedding_source_text)

        episode = ClinicalEpisode(
            episode_uid=episode_uid,
            patient_uid=patient_uid,
            timestamp=timestamp or datetime.datetime.utcnow(),
            encounter_type=encounter_type,
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            vital_signs=vital_signs or {},
            diagnosis=diagnosis,
            prescribed_medications=prescribed_medications,
            physician_notes=physician_notes,
            lab_results=lab_results or {},
            embedding=embedding_vec,
            severity_score=severity_score
        )
        self.db.add(episode)
        self.db.commit()
        self.db.refresh(episode)
        logger.info(f"Recorded Episodic Memory {episode_uid} for Patient {patient_uid}")
        return episode

    def recall_relevant_episodes(
        self,
        patient_uid: str,
        current_presentation: str,
        top_k: int = 5,
        recency_weight: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        Recalls past episodes using hybrid Vector Similarity + Temporal Decay Scoring.
        Score = (1 - recency_weight) * VectorSimilarity + recency_weight * RecencyScore
        """
        results = self.store.vector_search_episodes(patient_uid, current_presentation, top_k=top_k * 2)
        
        now = datetime.datetime.utcnow()
        scored_memories = []

        for ep, vector_sim in results:
            # Calculate days passed
            days_passed = max(1, (now - ep.timestamp).days)
            recency_score = 1.0 / (1.0 + 0.005 * days_passed) # Soft exponential decay
            
            final_composite_score = ((1.0 - recency_weight) * vector_sim) + (recency_weight * recency_score)
            
            scored_memories.append({
                "episode_uid": ep.episode_uid,
                "timestamp": ep.timestamp.isoformat(),
                "encounter_type": ep.encounter_type,
                "chief_complaint": ep.chief_complaint,
                "symptoms": ep.symptoms,
                "diagnosis": ep.diagnosis,
                "prescribed_medications": ep.prescribed_medications,
                "physician_notes": ep.physician_notes,
                "lab_results": ep.lab_results,
                "vector_similarity": round(vector_sim, 4),
                "recency_score": round(recency_score, 4),
                "composite_score": round(final_composite_score, 4)
            })

        # Re-sort by composite score
        scored_memories.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored_memories[:top_k]

    def get_all_episodes(self, patient_uid: str) -> List[ClinicalEpisode]:
        """Returns chronological list of all patient encounters."""
        return self.db.query(ClinicalEpisode).filter(
            ClinicalEpisode.patient_uid == patient_uid
        ).order_by(ClinicalEpisode.timestamp.asc()).all()
