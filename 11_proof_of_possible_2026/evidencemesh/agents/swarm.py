"""
Multi-Agent Swarm Orchestrator.
Coordinates Extractor, Verifier, Cross-Examiner, Bayesian Calibrator, and Merkle Ledger.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from evidencemesh.models import (
    VerificationRequest,
    VerificationResponse,
    AtomicClaim,
    VerificationStatus
)
from evidencemesh.core.claim_decomposer import ClaimDecomposer
from evidencemesh.core.causal_graph import CausalGraph
from evidencemesh.core.bayesian_calibrator import BayesianCalibrator
from evidencemesh.core.merkle_ledger import MerkleProofLedger
from evidencemesh.core.verifier import EvidenceVerifier
from evidencemesh.knowledge.corpus import KnowledgeCorpus
from evidencemesh.agents.extractor import ExtractorAgent
from evidencemesh.agents.cross_examiner import CrossExaminerAgent
from evidencemesh.agents.synthesizer import SynthesizerAgent
from evidencemesh.config import settings


class EvidenceMeshSwarm:
    """
    Main swarm coordinator that runs multi-agent verification pipeline.
    """

    def __init__(self):
        self.corpus = KnowledgeCorpus()
        self.verifier = EvidenceVerifier(self.corpus)
        self.extractor = ExtractorAgent()
        self.cross_examiner = CrossExaminerAgent()
        self.synthesizer = SynthesizerAgent()
        self.ledger = MerkleProofLedger()

    def verify(self, req: VerificationRequest) -> VerificationResponse:
        start_time = time.perf_counter()
        session_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"
        audit_trace: List[Dict[str, Any]] = []

        # Step 1: Extractor Agent
        claims, extract_audit = self.extractor.process(req.text_content)
        audit_trace.append(extract_audit)

        # Step 2: Individual Atomic Claim Verification
        for claim in claims:
            self.verifier.verify_claim(claim, domain=req.domain or "general")

        audit_trace.append({
            "agent": "EvidenceGroundingEngine",
            "role": "Corpus & Rule Verification",
            "grounded_count": len(claims),
            "summary": f"Grounded {len(claims)} propositions against peer-reviewed corpus."
        })

        # Step 3: Initialize Causal Graph DAG
        graph = CausalGraph()
        for claim in claims:
            graph.add_claim(claim)

        # Step 4: Adversarial Cross-Examiner
        if req.deep_cross_examination:
            edges, cross_audit = self.cross_examiner.cross_examine(claims, graph)
            audit_trace.append(cross_audit)
        else:
            edges = []

        # Step 5: Bayesian Calibration
        calibrator = BayesianCalibrator(
            prior_alpha=settings.DEFAULT_PRIOR_ALPHA * (1.0 - req.prior_skepticism + 0.5),
            prior_beta=settings.DEFAULT_PRIOR_BETA * (req.prior_skepticism + 0.5)
        )
        calib_result = calibrator.calibrate_claims(claims)

        audit_trace.append({
            "agent": "BayesianEpistemicCalibrator",
            "role": "Uncertainty & Calibration Scoring",
            "calibrated_prob": calib_result.calibrated_probability,
            "ece": calib_result.expected_calibration_error,
            "brier": calib_result.brier_score,
            "ci_95": [calib_result.credible_interval_low_95, calib_result.credible_interval_high_95],
            "summary": f"Computed 95% Credible Interval [{calib_result.credible_interval_low_95:.2f}, {calib_result.credible_interval_high_95:.2f}] with ECE {calib_result.expected_calibration_error:.3f}."
        })

        # Step 6: Consensus Synthesizer
        overall_status, risk_level, synth_audit = self.synthesizer.synthesize(claims, graph, calib_result)
        audit_trace.append(synth_audit)

        # Step 7: Cryptographic Proof Certificate
        proof_cert = self.ledger.build_certificate(
            claims=claims,
            domain=req.domain or "general",
            calibrated_confidence=calib_result.calibrated_probability
        )

        audit_trace.append({
            "agent": "CryptographicMerkleLedger",
            "role": "Tamper-Evident Proof Generation",
            "merkle_root": proof_cert.merkle_root,
            "cert_id": proof_cert.certificate_id,
            "signature": proof_cert.audit_signature,
            "summary": f"Generated cryptographic Proof Certificate '{proof_cert.certificate_id}' with SHA-256 Merkle root {proof_cert.merkle_root[:16]}..."
        })

        exec_time_ms = max(0.01, round((time.perf_counter() - start_time) * 1000, 2))

        return VerificationResponse(
            session_id=session_id,
            original_text=req.text_content,
            overall_status=overall_status,
            calibrated_confidence=calib_result.calibrated_probability,
            epistemic_risk=risk_level,
            atomic_claims=claims,
            causal_edges=graph.edges,
            calibration_metrics=calib_result,
            proof_certificate=proof_cert,
            audit_trace=audit_trace,
            execution_time_ms=exec_time_ms
        )
