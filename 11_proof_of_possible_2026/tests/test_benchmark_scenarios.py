import pytest
from evidencemesh.knowledge.benchmark_scenarios import BENCHMARK_SCENARIOS
from evidencemesh.agents.swarm import EvidenceMeshSwarm
from evidencemesh.models import VerificationRequest, VerificationStatus


def test_all_benchmark_scenarios_execute_successfully():
    swarm = EvidenceMeshSwarm()

    for sc in BENCHMARK_SCENARIOS:
        req = VerificationRequest(text_content=sc.sample_text, domain="general", deep_cross_examination=True)
        res = swarm.verify(req)

        assert len(res.atomic_claims) > 0
        assert res.proof_certificate.certificate_id.startswith("CERT-EM-")
        assert res.execution_time_ms >= 0.0
        assert res.calibration_metrics.calibrated_probability >= 0.0
