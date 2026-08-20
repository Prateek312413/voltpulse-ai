import pytest
from evidencemesh.agents.swarm import EvidenceMeshSwarm
from evidencemesh.models import VerificationRequest, VerificationStatus


def test_swarm_clinical_contradiction_detection():
    swarm = EvidenceMeshSwarm()
    text = (
        "Empagliflozin reduces the risk of sustained decline in eGFR by 28% in chronic kidney disease patients. "
        "The patient was prescribed Amoxicillin for an acute sinus infection; "
        "however, the patient has a documented severe IgE-mediated anaphylactic reaction to penicillin."
    )
    req = VerificationRequest(text_content=text, domain="biomedical", prior_skepticism=0.5, deep_cross_examination=True)
    res = swarm.verify(req)

    assert len(res.atomic_claims) >= 3
    assert res.proof_certificate.contradiction_count >= 1
    assert res.overall_status in [VerificationStatus.CONTRADICTED, VerificationStatus.REFUTED]
    assert len(res.audit_trace) >= 5


def test_swarm_energy_density_verification():
    swarm = EvidenceMeshSwarm()
    text = "Our new sulfide-based solid-state battery cell achieves 450 Wh/kg gravimetric energy density at 25°C."
    req = VerificationRequest(text_content=text, domain="energy", prior_skepticism=0.3)
    res = swarm.verify(req)

    assert len(res.atomic_claims) >= 1
    assert res.atomic_claims[0].status == VerificationStatus.VERIFIED
    assert res.calibrated_confidence > 0.60
