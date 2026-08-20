import pytest
from evidencemesh.core.bayesian_calibrator import BayesianCalibrator
from evidencemesh.models import AtomicClaim, VerificationStatus, EvidenceSource


def test_bayesian_calibrator_credible_intervals():
    calibrator = BayesianCalibrator(prior_alpha=2.0, prior_beta=2.0)
    claims = [
        AtomicClaim(
            claim_id="CLM-001",
            text="High confidence claim",
            status=VerificationStatus.VERIFIED,
            confidence_score=0.95,
            supporting_evidence=[EvidenceSource(source_id="S1", title="Paper", domain="gen", relevance_score=0.9, snippet="", reliability_weight=0.98)]
        ),
        AtomicClaim(
            claim_id="CLM-002",
            text="Second verified claim",
            status=VerificationStatus.VERIFIED,
            confidence_score=0.90,
            supporting_evidence=[EvidenceSource(source_id="S2", title="Paper", domain="gen", relevance_score=0.9, snippet="", reliability_weight=0.95)]
        )
    ]

    res = calibrator.calibrate_claims(claims)
    assert res.calibrated_probability > 0.65
    assert res.credible_interval_low_95 < res.calibrated_probability < res.credible_interval_high_95
    assert res.expected_calibration_error >= 0.0
    assert res.brier_score >= 0.0


def test_bayesian_calibrator_empty():
    calibrator = BayesianCalibrator()
    res = calibrator.calibrate_claims([])
    assert res.calibrated_probability == 0.5
    assert res.epistemic_entropy == 1.0
