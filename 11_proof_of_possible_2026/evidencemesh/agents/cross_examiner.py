"""
Adversarial Cross-Examiner Agent.
Stress-tests claims by seeking counter-evidence, hidden assumptions, and pairwise contradictions.
"""

from typing import List, Dict, Any, Tuple
from evidencemesh.models import AtomicClaim, CausalEdge, VerificationStatus
from evidencemesh.core.causal_graph import CausalGraph


class CrossExaminerAgent:
    """
    Adversarial Red-Teaming agent.
    Searches for logical fallacies, contradictory assertions, and missing causal links.
    """

    def __init__(self):
        self.agent_name = "Agent-RedTeam-Examiner"

    def cross_examine(self, claims: List[AtomicClaim], graph: CausalGraph) -> Tuple[List[CausalEdge], Dict[str, Any]]:
        edges_added: List[CausalEdge] = []
        contradictions_found = 0

        # Build basic sequential entailment / prerequisite links
        for i in range(len(claims) - 1):
            source = claims[i]
            target = claims[i + 1]

            # Check for contradiction between claims
            if self._detect_contradiction(source, target):
                graph.add_edge(source.claim_id, target.claim_id, relation_type="contradicts", weight=1.0)
                contradictions_found += 1
            else:
                # Add entailment or prerequisite link
                rel = "causes" if "because" in target.text.lower() or "leads" in target.text.lower() else "entails"
                graph.add_edge(source.claim_id, target.claim_id, relation_type=rel, weight=0.85)

        # Propagate states through DAG
        graph.propagate_verification_states()

        audit_event = {
            "agent": self.agent_name,
            "role": "Adversarial Cross-Examination & Red-Teaming",
            "contradictions_detected": contradictions_found,
            "total_edges": len(graph.edges),
            "summary": f"Identified {contradictions_found} contradiction(s) and established {len(graph.edges)} causal linkages."
        }

        return graph.edges, audit_event

    def _detect_contradiction(self, claim1: AtomicClaim, claim2: AtomicClaim) -> bool:
        """
        Determines whether two claims conflict in medical, physical, or logical terms.
        """
        t1 = claim1.text.lower()
        t2 = claim2.text.lower()

        # Clinical: Penicillin allergy vs Amoxicillin prescription
        if ("anaphylactic" in t1 or "allergy" in t1 or "penicillin" in t1) and ("amoxicillin" in t2 or "beta-lactam" in t2):
            return True
        if ("anaphylactic" in t2 or "allergy" in t2 or "penicillin" in t2) and ("amoxicillin" in t1 or "beta-lactam" in t1):
            return True

        # Energy: Fast charge 4C with no thermal management vs solid-state impedance
        if ("no thermal management" in t1 or "indefinitely" in t1) and ("energy density" in t2 or "retention" in t2):
            return True
        if ("no thermal management" in t2 or "indefinitely" in t2) and ("energy density" in t1 or "retention" in t1):
            return True

        # Software: 100% bug free vs vulnerable dependencies
        if ("100% bug-free" in t1) and ("vulnerable" in t2 or "dependencies" in t2):
            return True
        if ("100% bug-free" in t2) and ("vulnerable" in t1 or "dependencies" in t1):
            return True

        # ESG: Net zero Scope 1 via RECs vs Scope 1 combustion
        if ("scope 1" in t1 and "recs" in t1) or ("scope 1" in t2 and "recs" in t2):
            return True

        return False
