"""
Extractor Agent: Parses unstructured claims into atomic proposition units.
"""

from typing import List, Dict, Any, Tuple
from evidencemesh.models import AtomicClaim
from evidencemesh.core.claim_decomposer import ClaimDecomposer


class ExtractorAgent:
    """
    Agent responsible for isolating distinct assertions and assigning semantic structure.
    """

    def __init__(self):
        self.decomposer = ClaimDecomposer()
        self.agent_name = "Agent-Decomposer-01"

    def process(self, text: str) -> Tuple[List[AtomicClaim], Dict[str, Any]]:
        claims = self.decomposer.decompose(text)
        audit_event = {
            "agent": self.agent_name,
            "role": "Atomic Claim Decomposition",
            "extracted_count": len(claims),
            "summary": f"Extracted {len(claims)} atomic propositions from source text."
        }
        return claims, audit_event
