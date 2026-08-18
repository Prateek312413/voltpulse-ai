"""
Unit & Integration Tests for AegisMed 4-Tier Memory Hierarchy
"""

import pytest
import datetime
from aegismed.database.connection import get_db_session, init_db
from aegismed.database.models import Patient
from aegismed.database.seed_data import seed_all
from aegismed.memory import AgenticMemoryEngine, MemoryTier


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initializes and seeds database before running memory tests."""
    init_db()
    seed_all()


def test_tier1_working_memory_locks_and_thoughts():
    """Validates Working Memory ACID session creation, thought logging, and lock arbitration."""
    with get_db_session() as db:
        engine = AgenticMemoryEngine(db)
        session = engine.working.initialize_session("P-1001", {"complaint": "Acute fever"})
        
        assert session.session_id.startswith("sess_")
        assert session.status == "ACTIVE"
        assert session.version == 1

        # Test Lock Acquisition
        lock_ok = engine.working.acquire_lock(session.session_id, "TriageAgent")
        assert lock_ok is True
        
        # Test Second Agent Lock Contention
        lock_denied = engine.working.acquire_lock(session.session_id, "DiagnosticAgent")
        assert lock_denied is False

        # Release Lock
        engine.working.release_lock(session.session_id, "TriageAgent")
        lock_acquired_now = engine.working.acquire_lock(session.session_id, "DiagnosticAgent")
        assert lock_acquired_now is True

        # Test Thought Logging
        engine.working.record_agent_thought(
            session_id=session.session_id,
            agent_name="DiagnosticAgent",
            thought_text="Analyzing vital signs and historical markers.",
            step_type="REASONING"
        )
        
        refreshed = engine.working.get_session(session.session_id)
        assert len(refreshed.agent_thoughts) >= 1
        assert refreshed.agent_thoughts[0]["agent"] == "DiagnosticAgent"


def test_tier2_episodic_memory_vector_recall():
    """Validates Episodic Memory vector embedding and semantic recall."""
    with get_db_session() as db:
        engine = AgenticMemoryEngine(db)
        
        # Query for dental allergy symptoms
        recalled = engine.episodic.recall_relevant_episodes(
            patient_uid="P-1001",
            current_presentation="anaphylaxis swelling hives after dental amoxicillin antibiotic",
            top_k=3
        )
        
        assert len(recalled) >= 1
        top_match = recalled[0]
        assert "Allergy" in top_match["diagnosis"] or "Hypersensitivity" in top_match["diagnosis"]
        assert top_match["vector_similarity"] > 0.40


def test_tier3_semantic_guidelines_contraindications():
    """Validates Tier 3 Semantic Memory blocking dangerous drugs."""
    with get_db_session() as db:
        engine = AgenticMemoryEngine(db)
        
        alerts = engine.semantic.check_contraindications(
            candidate_medications=["Amoxicillin", "Azithromycin"],
            known_allergies=["Penicillin"],
            chronic_conditions=["Primary Hypertension"]
        )
        
        assert len(alerts) >= 1
        offending = [a["offending_agent"].lower() for a in alerts]
        assert "amoxicillin" in offending
        assert "azithromycin" not in offending


def test_tier4_reflective_meta_insights():
    """Validates autonomous pattern synthesis across longitudinal encounters."""
    with get_db_session() as db:
        engine = AgenticMemoryEngine(db)
        insights = engine.reflective.generate_patient_reflections("P-1001")
        
        assert len(insights) >= 1
        types = [i.insight_type for i in insights]
        assert "ADVERSE_REACTION_PATTERN" in types
