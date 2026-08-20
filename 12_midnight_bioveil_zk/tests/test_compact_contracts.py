"""
Unit tests for Midnight Compact smart contract logic and circuit constraints
"""

import pytest
from backend.zk_engine import (
    BioVeilZKProver,
    BioVeilZKVerifier,
    compute_biomarker_hash,
    compute_condition_mask
)
from backend.sample_data import get_initial_trials, get_sample_patients


def test_compact_eligibility_circuit_pass():
    trials = get_initial_trials()
    patients = get_sample_patients()
    
    oncology_trial = trials[0]
    eligible_patient = patients["elena_vance_eligible_oncology"]

    proof = BioVeilZKProver.generate_proof(
        trial_id=oncology_trial.trial_id,
        criteria=oncology_trial.criteria,
        patient=eligible_patient
    )

    assert proof.verification_status is True
    assert len(proof.circuit_constraints) == 5
    for c in proof.circuit_constraints:
        assert c.evaluated_truth is True
    assert proof.nullifier_hash.startswith("0x")
    assert proof.public_commitment.startswith("0x")


def test_compact_eligibility_circuit_age_rejection():
    trials = get_initial_trials()
    patients = get_sample_patients()
    
    oncology_trial = trials[0]
    ineligible_age_patient = patients["marcus_chen_ineligible_age"]

    proof = BioVeilZKProver.generate_proof(
        trial_id=oncology_trial.trial_id,
        criteria=oncology_trial.criteria,
        patient=ineligible_age_patient
    )

    assert proof.verification_status is False
    age_constraint = next(c for c in proof.circuit_constraints if c.name == "ZK_RANGE_AGE_INCLUSION")
    assert age_constraint.evaluated_truth is False


def test_compact_eligibility_circuit_renal_rejection():
    trials = get_initial_trials()
    patients = get_sample_patients()
    
    oncology_trial = trials[0]
    ineligible_renal_patient = patients["sarah_jenkins_ineligible_renal"]

    proof = BioVeilZKProver.generate_proof(
        trial_id=oncology_trial.trial_id,
        criteria=oncology_trial.criteria,
        patient=ineligible_renal_patient
    )

    assert proof.verification_status is False
    renal_constraint = next(c for c in proof.circuit_constraints if c.name == "ZK_THRESHOLD_RENAL_SAFETY")
    assert renal_constraint.evaluated_truth is False


def test_on_chain_verifier_validation():
    valid, msg = BioVeilZKVerifier.verify_on_chain(
        trial_id="0x4f8a1290bb34c980a421c002fa883901bca7290192e482710492817290184a21",
        nullifier_hash="0x00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff",
        public_commitment="0xaabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
        proof_bytes_hex="0x01" + "a" * 128
    )
    assert valid is True
    assert "Satisfied" in msg


def test_on_chain_verifier_malformed_proof():
    valid, msg = BioVeilZKVerifier.verify_on_chain(
        trial_id="0x4f8a",
        nullifier_hash="invalid_hash",
        public_commitment="0x00",
        proof_bytes_hex="0x02_bad_header"
    )
    assert valid is False
