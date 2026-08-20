"""
End-to-end API tests for BioVeil ZK FastAPI server
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_network_stats():
    res = client.get("/api/network/stats")
    assert res.status_code == 200
    data = res.json()
    assert "current_block_height" in data
    assert data["network_name"].startswith("Midnight")


def test_get_trials_list():
    res = client.get("/api/trials")
    assert res.status_code == 200
    trials = res.json()
    assert len(trials) >= 4


def test_generate_and_submit_zk_proof_e2e():
    # 1. Get sample patients and trials
    trials_res = client.get("/api/trials")
    trials = trials_res.json()
    trial = trials[0]

    patients_res = client.get("/api/patients/samples")
    patients = patients_res.json()
    patient = patients["elena_vance_eligible_oncology"]

    # 2. Generate ZK Proof
    proof_req = {
        "trial_id": trial["trial_id"],
        "patient_profile": patient,
        "include_viewing_key": True
    }
    proof_res = client.post("/api/zk/generate-proof", json=proof_req)
    assert proof_res.status_code == 200
    proof_data = proof_res.json()
    assert proof_data["verification_status"] is True

    # 3. Submit proof to Midnight
    sub_req = {
        "trial_id": trial["trial_id"],
        "nullifier_hash": proof_data["nullifier_hash"],
        "public_commitment": proof_data["public_commitment"],
        "proof_bytes_hex": proof_data["proof_bytes_hex"],
        "shielded_address": patient["midnight_shielded_address"]
    }
    sub_res = client.post("/api/zk/submit-proof", json=sub_req)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["success"] is True


def test_inspect_audit_grant():
    grants_res = client.get("/api/auditor/grants")
    assert grants_res.status_code == 200
    grants = grants_res.json()
    assert len(grants) > 0

    grant_id = grants[0]["grant_id"]
    inspect_res = client.get(f"/api/auditor/inspect/{grant_id}")
    assert inspect_res.status_code == 200
    data = inspect_res.json()
    assert data["is_valid"] is True
    assert "decrypted_cohort_metrics" in data


def test_get_compact_source_files():
    res = client.get("/api/contracts/compact-source")
    assert res.status_code == 200
    sources = res.json()
    assert "BioVeilZK.compact" in sources
    assert "ShieldEscrow.compact" in sources
    assert "AuditCompliance.compact" in sources
