import pytest
from evidencemesh.core.merkle_ledger import MerkleProofLedger
from evidencemesh.models import AtomicClaim, VerificationStatus


def test_merkle_proof_ledger_deterministic_root():
    ledger = MerkleProofLedger()
    claims = [
        AtomicClaim(claim_id="CLM-001", text="Empagliflozin SGLT2", status=VerificationStatus.VERIFIED, confidence_score=0.95),
        AtomicClaim(claim_id="CLM-002", text="CKD eGFR decline 28%", status=VerificationStatus.VERIFIED, confidence_score=0.92)
    ]

    cert1 = ledger.build_certificate(claims, domain="biomedical", calibrated_confidence=0.93)
    cert2 = ledger.build_certificate(claims, domain="biomedical", calibrated_confidence=0.93)

    assert cert1.merkle_root == cert2.merkle_root
    assert cert1.claim_count == 2
    assert cert1.is_tamper_evident_valid is True
    assert ledger.verify_certificate_integrity(cert1, claims) is True


def test_merkle_tamper_detection():
    ledger = MerkleProofLedger()
    claims = [
        AtomicClaim(claim_id="CLM-001", text="Original unaltered claim", status=VerificationStatus.VERIFIED, confidence_score=0.9)
    ]
    cert = ledger.build_certificate(claims, domain="general", calibrated_confidence=0.9)

    # Tamper with the claim text
    tampered_claims = [
        AtomicClaim(claim_id="CLM-001", text="Tampered malicious claim", status=VerificationStatus.VERIFIED, confidence_score=0.9)
    ]

    # Verify that integrity check catches the tampering
    assert ledger.verify_certificate_integrity(cert, tampered_claims) is False
