"""
AegisMed 4-Tier Memory Engine Package
Integrates Working, Episodic, Semantic, and Reflective Memory into a unified system.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from aegismed.memory.base import MemoryTier, MemoryNode, MemoryEdge, MemoryGraph
from aegismed.memory.cockroach_store import CockroachMemoryStore
from aegismed.memory.working_memory import WorkingMemoryManager
from aegismed.memory.episodic_memory import EpisodicMemoryManager
from aegismed.memory.semantic_memory import SemanticMemoryManager
from aegismed.memory.reflective_memory import ReflectiveMemoryManager
from aegismed.database.models import Patient, SemanticGuideline


class AgenticMemoryEngine:
    """The central unified memory coordinator for the AegisMed agent swarm."""

    def __init__(self, db: Session):
        self.db = db
        self.store = CockroachMemoryStore(db)
        self.working = WorkingMemoryManager(db)
        self.episodic = EpisodicMemoryManager(db)
        self.semantic = SemanticMemoryManager(db)
        self.reflective = ReflectiveMemoryManager(db)

    def generate_memory_graph(self, patient_uid: str, session_id: Optional[str] = None) -> MemoryGraph:
        """
        Constructs a complete interconnected graph of Working, Episodic, Semantic,
        and Reflective memory nodes for visualization in the clinician interface.
        """
        nodes: List[MemoryNode] = []
        edges: List[MemoryEdge] = []

        # 1. Patient Root Node
        patient = self.db.query(Patient).filter(Patient.patient_uid == patient_uid).first()
        if patient:
            p_node = MemoryNode(
                id=f"p_{patient.patient_uid}",
                label=f"Patient: {patient.name} ({patient.age}y {patient.gender})",
                tier=MemoryTier.WORKING,
                summary=f"Allergies: {', '.join(patient.allergies or ['None'])}; Conditions: {', '.join(patient.chronic_conditions or ['None'])}",
                data={"allergies": patient.allergies, "conditions": patient.chronic_conditions}
            )
            nodes.append(p_node)

        # 2. Working Memory Session Node (Tier 1)
        if session_id:
            session = self.working.get_session(session_id)
            if session:
                sess_node = MemoryNode(
                    id=f"sess_{session.session_id}",
                    label=f"Working Session ({session.current_acuity})",
                    tier=MemoryTier.WORKING,
                    timestamp=session.created_at.isoformat() if session.created_at else None,
                    summary=f"Active Agent: {session.active_agent}; Version: {session.version}; Status: {session.status}",
                    data={"hypotheses": session.active_hypotheses, "acuity": session.current_acuity}
                )
                nodes.append(sess_node)
                if patient:
                    edges.append(MemoryEdge(source=f"p_{patient.patient_uid}", target=sess_node.id, relationship="ACTIVE_CONSULTATION"))

        # 3. Episodic Memory Nodes (Tier 2)
        episodes = self.episodic.get_all_episodes(patient_uid)
        for ep in episodes:
            ep_node = MemoryNode(
                id=f"ep_{ep.episode_uid}",
                label=f"Episode ({ep.timestamp.strftime('%b %d, %Y')})",
                tier=MemoryTier.EPISODIC,
                timestamp=ep.timestamp.isoformat(),
                summary=f"Dx: {ep.diagnosis or ep.chief_complaint}; Prescribed: {len(ep.prescribed_medications or [])} meds",
                data={
                    "chief_complaint": ep.chief_complaint,
                    "diagnosis": ep.diagnosis,
                    "meds": ep.prescribed_medications,
                    "vitals": ep.vital_signs
                }
            )
            nodes.append(ep_node)
            if patient:
                edges.append(MemoryEdge(source=f"p_{patient.patient_uid}", target=ep_node.id, relationship="HISTORICAL_ENCOUNTER"))

        # 4. Reflective Memory Nodes (Tier 4)
        insights = self.reflective.get_insights(patient_uid)
        for ins in insights:
            ins_node = MemoryNode(
                id=f"ins_{ins.insight_uid}",
                label=f"Reflective Insight: {ins.insight_type}",
                tier=MemoryTier.REFLECTIVE,
                timestamp=ins.created_at.isoformat(),
                summary=ins.headline,
                data={
                    "synthesis": ins.detailed_synthesis,
                    "confidence": ins.confidence_score,
                    "guidance": ins.actionable_guidance
                }
            )
            nodes.append(ins_node)
            # Link to source episodes
            for ep_uid in (ins.source_episode_uids or []):
                edges.append(MemoryEdge(source=f"ep_{ep_uid}", target=ins_node.id, relationship="SYNTHESIZED_FROM"))

        # 5. Semantic Guidelines (Tier 3)
        # Pull top relevant guidelines
        guidelines = self.db.query(SemanticGuideline).limit(5).all()
        for g in guidelines:
            g_node = MemoryNode(
                id=f"g_{g.rule_uid}",
                label=f"Guideline: {g.title[:35]}...",
                tier=MemoryTier.SEMANTIC,
                summary=g.description[:100] + "...",
                data={"entity_a": g.entity_a, "entity_b": g.entity_b, "risk": g.risk_level}
            )
            nodes.append(g_node)
            if session_id:
                edges.append(MemoryEdge(source=f"sess_{session_id}", target=g_node.id, relationship="SAFETY_EVALUATION"))

        return MemoryGraph(
            patient_uid=patient_uid,
            session_id=session_id,
            nodes=nodes,
            edges=edges,
            active_memory_count=len(nodes)
        )


__all__ = [
    "MemoryTier", "MemoryNode", "MemoryEdge", "MemoryGraph",
    "CockroachMemoryStore", "WorkingMemoryManager", "EpisodicMemoryManager",
    "SemanticMemoryManager", "ReflectiveMemoryManager", "AgenticMemoryEngine"
]
