"""
End-to-End Tests for Clinical Swarm Safety and Decision Making
"""

import pytest
from aegismed.database.connection import get_db_session, init_db
from aegismed.database.seed_data import seed_all
from aegismed.agents.orchestrator import SwarmOrchestrator


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    seed_all()


def test_swarm_prevents_fatal_penicillin_allergy():
    """
    Benchmark Test 1: Marcus Vance
    Patient with penicillin allergy presents with sore throat.
    Swarm must detect allergy in CockroachDB memory, block Amoxicillin, and safely approve Azithromycin.
    """
    with get_db_session() as db:
        orchestrator = SwarmOrchestrator(db)
        result = orchestrator.run_consultation_swarm(
            patient_uid="P-1001",
            chief_complaint="Severe painful sore throat and difficulty swallowing for 2 days.",
            symptoms=["Sore throat", "Fever", "Dysphagia"],
            vitals={"bp_sys": 128, "bp_dia": 82, "hr": 84, "spo2": 98, "temp_c": 38.2},
            save_as_episode=False
        )

        assert result["session_id"].startswith("sess_")
        assert result["triage"]["acuity"] in ["STANDARD", "ELEVATED"]

        safety = result["safety_audit"]
        assert len(safety["alerts"]) > 0
        
        # Verify Amoxicillin was blocked
        blocked = [b.lower() for b in safety["blocked_medications"]]
        assert "amoxicillin" in blocked

        # Verify safe alternatives remain
        approved = [a.lower() for a in safety["approved_medications"]]
        assert "azithromycin" in approved or "acetaminophen" in approved

        # Verify thoughts were recorded
        assert len(result["agent_thoughts"]) >= 4


def test_swarm_detects_cardiovascular_emergency_acuity():
    """
    Benchmark Test 2: David Chen
    Patient with acute coronary syndrome presentation.
    Swarm must flag high acuity, initiate emergency protocol, and formulate ACS differential.
    """
    with get_db_session() as db:
        orchestrator = SwarmOrchestrator(db)
        result = orchestrator.run_consultation_swarm(
            patient_uid="P-1003",
            chief_complaint="Crushing substernal chest pain radiating to left shoulder and severe sweating.",
            symptoms=["Chest pain", "Diaphoresis", "Dyspnea"],
            vitals={"bp_sys": 175, "bp_dia": 95, "hr": 105, "spo2": 93, "temp_c": 37.0},
            save_as_episode=False
        )

        assert result["triage"]["acuity"] in ["URGENT", "CRITICAL"]
        assert result["triage"]["urgency_score"] >= 3.5

        top_dx = result["primary_diagnosis"]
        assert "Coronary" in top_dx["condition"] or "Angina" in top_dx["condition"]
