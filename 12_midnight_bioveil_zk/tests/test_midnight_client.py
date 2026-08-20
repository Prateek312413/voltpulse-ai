"""
Integration tests for Midnight Network Client and Dual-State Ledger
"""

import pytest
from backend.midnight_client import MidnightNetworkClient
from backend.data_models import ClinicalTrialModel, EligibilityCriteriaModel, TrialStatusEnum
from backend.zk_engine import compute_biomarker_hash


def test_midnight_client_initialization():
    client = MidnightNetworkClient()
    stats = client.get_network_stats()
    assert stats.current_block_height >= 1420
    assert len(client.get_all_trials()) >= 4
    assert len(client.blocks) > 0


def test_submit_zk_enrollment_and_nullifier_protection():
    client = MidnightNetworkClient()
    trials = client.get_all_trials()
    trial = trials[0]
    initial_enrolled = trial.enrolled_count

    nullifier = "0x00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
    commitment = "0xaabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
    proof_bytes = "0x01" + "f" * 128
    addr = "midnight1z_patient_test_8819a"

    # First enrollment succeeds
    success, msg, tx = client.submit_zk_enrollment(
        trial_id=trial.trial_id,
        nullifier_hash=nullifier,
        public_commitment=commitment,
        proof_bytes_hex=proof_bytes,
        shielded_address=addr
    )
    assert success is True
    assert trial.enrolled_count == initial_enrolled + 1
    assert tx is not None
    assert tx.status == "CONFIRMED"

    # Double enrollment with same nullifier must fail
    dup_success, dup_msg, _ = client.submit_zk_enrollment(
        trial_id=trial.trial_id,
        nullifier_hash=nullifier,
        public_commitment=commitment,
        proof_bytes_hex=proof_bytes,
        shielded_address=addr
    )
    assert dup_success is False
    assert "Nullifier collision" in dup_msg


def test_claim_milestone_payout():
    client = MidnightNetworkClient()
    trials = client.get_all_trials()
    trial = trials[0]

    nullifier = "0x99887766554433221100aabbccddeeff99887766554433221100aabbccddeeff"
    client.submit_zk_enrollment(
        trial_id=trial.trial_id,
        nullifier_hash=nullifier,
        public_commitment="0x0011",
        proof_bytes_hex="0x01" + "a" * 128,
        shielded_address="midnight1z_patient_test_8819a"
    )

    initial_escrow = trial.escrow_deposit_night
    success, msg, amount, tx = client.claim_milestone_payout(
        nullifier_hash=nullifier,
        checkpoint_id="CHECKPOINT_1",
        completion_secret_hex="0x00112233",
        shielded_recipient_address="midnight1z_patient_test_8819a"
    )

    assert success is True
    assert amount == trial.milestone_reward_night
    assert trial.escrow_deposit_night == initial_escrow - amount
    assert tx.circuit_invoked == "submitMilestoneProofAndClaimStipend"
