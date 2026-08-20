"""
Unit tests for BioVeil ZK Proving Engine and Poseidon Hash Primitives
"""

import pytest
from backend.zk_engine import (
    poseidon_hash,
    compute_biomarker_hash,
    compute_condition_mask,
    CONDITION_FLAGS,
    BioVeilZKProver
)
from backend.sample_data import get_initial_trials, get_sample_patients


def test_poseidon_hash_deterministic():
    h1 = poseidon_hash("MIDNIGHT_CIRCUIT", 1420, "TEST_LOCUS")
    h2 = poseidon_hash("MIDNIGHT_CIRCUIT", 1420, "TEST_LOCUS")
    assert h1 == h2
    assert h1.startswith("0x")
    assert len(h1) == 66


def test_compute_condition_mask():
    conds = ["ACTIVE_MALIGNANCY_OTHER", "END_STAGE_RENAL_DISEASE"]
    mask = compute_condition_mask(conds)
    expected = CONDITION_FLAGS["ACTIVE_MALIGNANCY_OTHER"] | CONDITION_FLAGS["END_STAGE_RENAL_DISEASE"]
    assert mask == expected


def test_biomarker_hash_consistency():
    h1 = compute_biomarker_hash("HER2_POS_EXON20")
    h2 = compute_biomarker_hash("her2_pos_exon20")
    assert h1 == h2


def test_zk_proof_proving_time():
    trials = get_initial_trials()
    patients = get_sample_patients()
    
    proof = BioVeilZKProver.generate_proof(
        trial_id=trials[0].trial_id,
        criteria=trials[0].criteria,
        patient=patients["elena_vance_eligible_oncology"]
    )
    assert proof.proving_time_ms > 0
    assert proof.proof_id.startswith("zkproof_")
