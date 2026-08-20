"""
Consensus Synthesizer Agent.
Harmonizes agent debate, resolves DAG dependencies, and assigns the macro verification verdict.
"""

from typing import List, Dict, Any, Tuple
from evidencemesh.models import AtomicClaim, VerificationStatus, BayesianCalibrationResult
from evidencemesh.core.causal_graph import CausalGraph


class SynthesizerAgent:
    """
    Consensus Synthesizer Agent.
    Aggregates atomic claim verifications, contradiction counts, and Bayesian outputs into an authoritative verdict.
    """

    def __init__(self):
        self.agent_name = "Agent-Consensus-Synthesizer"

    def synthesize(
        self,
        claims: List[AtomicClaim],
        graph: CausalGraph,
        calib: BayesianCalibrationResult
    ) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        if not claims:
            return VerificationStatus.UNCERTAIN, "HIGH", {"agent": self.agent_name, "summary": "No claims evaluated."}

        verified_count = sum(1 for c in claims if c.status == VerificationStatus.VERIFIED)
        refuted_count = sum(1 for c in claims if c.status == VerificationStatus.REFUTED)
        contradicted_count = sum(1 for c in claims if c.status == VerificationStatus.CONTRADICTED) or graph.get_contradiction_count()

        # Decision Matrix
        if refuted_count > 0 or contradicted_count > 0:
            if refuted_count > 0 and contradicted_count > 0:
                overall_status = VerificationStatus.CONTRADICTED
                risk = "CRITICAL"
            elif contradicted_count > 0:
                overall_status = VerificationStatus.CONTRADICTED
                risk = "CRITICAL"
            else:
                overall_status = VerificationStatus.REFUTED
                risk = "HIGH"
        elif verified_count == len(claims) and calib.calibrated_probability >= 0.75:
            overall_status = VerificationStatus.VERIFIED
            risk = "LOW"
        elif verified_count > 0:
            overall_status = VerificationStatus.VERIFIED if calib.calibrated_probability >= 0.65 else VerificationStatus.UNCERTAIN
            risk = "MODERATE"
        else:
            overall_status = VerificationStatus.UNCERTAIN
            risk = "HIGH"

        audit_event = {
            "agent": self.agent_name,
            "role": "Consensus Verdict Synthesis",
            "overall_status": overall_status.value,
            "epistemic_risk": risk,
            "verified_claims": verified_count,
            "refuted_claims": refuted_count,
            "contradictions": contradicted_count,
            "calibrated_probability": calib.calibrated_probability,
            "summary": f"Verdict: {overall_status.value} with {risk} Epistemic Risk (Calibrated Confidence: {calib.calibrated_probability:.1%})."
        }

        return overall_status, risk, audit_event
