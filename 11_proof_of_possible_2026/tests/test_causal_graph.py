import pytest
from evidencemesh.core.causal_graph import CausalGraph
from evidencemesh.models import AtomicClaim, VerificationStatus


def test_causal_graph_dag_and_topological_sort():
    graph = CausalGraph()
    c1 = AtomicClaim(claim_id="CLM-001", text="Prerequisite Claim A", status=VerificationStatus.VERIFIED)
    c2 = AtomicClaim(claim_id="CLM-002", text="Dependent Claim B", status=VerificationStatus.VERIFIED)
    c3 = AtomicClaim(claim_id="CLM-003", text="Final Claim C", status=VerificationStatus.VERIFIED)

    graph.add_claim(c1)
    graph.add_claim(c2)
    graph.add_claim(c3)

    graph.add_edge("CLM-001", "CLM-002", relation_type="prerequisite_of")
    graph.add_edge("CLM-002", "CLM-003", relation_type="entails")

    order = graph.topological_sort()
    assert order == ["CLM-001", "CLM-002", "CLM-003"]
    assert graph.detect_cycles() == []


def test_causal_graph_cycle_detection():
    graph = CausalGraph()
    c1 = AtomicClaim(claim_id="CLM-001", text="Claim 1")
    c2 = AtomicClaim(claim_id="CLM-002", text="Claim 2")
    graph.add_claim(c1)
    graph.add_claim(c2)

    graph.add_edge("CLM-001", "CLM-002", relation_type="causes")
    graph.add_edge("CLM-002", "CLM-001", relation_type="causes")

    cycles = graph.detect_cycles()
    assert len(cycles) > 0


def test_contradiction_propagation():
    graph = CausalGraph()
    c1 = AtomicClaim(claim_id="CLM-001", text="Penicillin allergy", status=VerificationStatus.VERIFIED)
    c2 = AtomicClaim(claim_id="CLM-002", text="Prescribed Amoxicillin", status=VerificationStatus.VERIFIED)
    graph.add_claim(c1)
    graph.add_claim(c2)

    graph.add_edge("CLM-001", "CLM-002", relation_type="contradicts")
    graph.propagate_verification_states()

    assert graph.claims["CLM-002"].status == VerificationStatus.CONTRADICTED
    assert graph.get_contradiction_count() == 1
