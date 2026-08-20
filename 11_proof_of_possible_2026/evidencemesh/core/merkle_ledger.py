"""
Cryptographic Merkle Evidence Tree and Proof Ledger Engine.
Produces immutable SHA-256 Merkle root proofs, audit signatures, and tamper-evident certificates.
"""

import hashlib
import json
import uuid
from typing import List, Dict, Any, Tuple
from evidencemesh.models import ProofCertificate, AtomicClaim, VerificationStatus
from evidencemesh.config import settings


class MerkleProofLedger:
    """
    Constructs a deterministic SHA-256 Merkle tree over verified atomic claims,
    their citation hashes, and Bayesian calibration outputs.
    """

    def __init__(self):
        self.salt = settings.CRYPTO_DOMAIN

    def build_certificate(
        self,
        claims: List[AtomicClaim],
        domain: str = "general",
        calibrated_confidence: float = 0.5
    ) -> ProofCertificate:
        """
        Generates a cryptographic Proof Certificate with Merkle root hash.
        """
        if not claims:
            empty_hash = self._hash_leaf({"empty": True})
            return ProofCertificate(
                certificate_id=f"PROOF-{uuid.uuid4().hex[:10].upper()}",
                claim_root_hash=empty_hash,
                merkle_root=empty_hash,
                claim_count=0,
                verified_count=0,
                contradiction_count=0,
                overall_confidence=0.5,
                epistemic_risk_level="HIGH",
                domain=domain,
                leaf_hashes=[empty_hash],
                audit_signature=f"SIG-SHA256-{empty_hash[:16]}",
                is_tamper_evident_valid=True
            )

        # 1. Generate canonical leaf hashes for each atomic claim
        leaf_hashes: List[str] = []
        verified_count = 0
        contradiction_count = 0

        for claim in claims:
            if claim.status == VerificationStatus.VERIFIED:
                verified_count += 1
            elif claim.status in [VerificationStatus.CONTRADICTED, VerificationStatus.REFUTED]:
                contradiction_count += 1

            leaf_dict = {
                "claim_id": claim.claim_id,
                "text": claim.text,
                "status": claim.status.value,
                "confidence": claim.confidence_score,
                "epistemic_uncertainty": claim.epistemic_uncertainty,
                "citations": [c.doi_or_url or c.title for c in claim.supporting_evidence]
            }
            leaf_hashes.append(self._hash_leaf(leaf_dict))

        # 2. Build Merkle Root
        merkle_root = self._compute_merkle_root(leaf_hashes)

        # 3. Determine Epistemic Risk Level
        if calibrated_confidence >= 0.80 and contradiction_count == 0:
            risk_level = "LOW"
        elif calibrated_confidence >= 0.60:
            risk_level = "MODERATE"
        elif calibrated_confidence >= 0.35:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # 4. Generate deterministic audit signature
        raw_sig = f"{merkle_root}:{domain}:{verified_count}:{calibrated_confidence}:{self.salt}"
        audit_sig = "SIG-" + hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:24].upper()

        cert_id = f"CERT-EM-{uuid.uuid4().hex[:8].upper()}"

        return ProofCertificate(
            certificate_id=cert_id,
            claim_root_hash=leaf_hashes[0] if leaf_hashes else merkle_root,
            merkle_root=merkle_root,
            claim_count=len(claims),
            verified_count=verified_count,
            contradiction_count=contradiction_count,
            overall_confidence=round(calibrated_confidence, 4),
            epistemic_risk_level=risk_level,
            domain=domain,
            leaf_hashes=leaf_hashes,
            audit_signature=audit_sig,
            is_tamper_evident_valid=True
        )

    def verify_certificate_integrity(self, cert: ProofCertificate, claims: List[AtomicClaim]) -> bool:
        """
        Validates that the certificate's Merkle root exactly matches the computed root
        over the claims, detecting any tampering.
        """
        if len(claims) != cert.claim_count:
            return False

        recomputed_leaf_hashes = []
        for claim in claims:
            leaf_dict = {
                "claim_id": claim.claim_id,
                "text": claim.text,
                "status": claim.status.value,
                "confidence": claim.confidence_score,
                "epistemic_uncertainty": claim.epistemic_uncertainty,
                "citations": [c.doi_or_url or c.title for c in claim.supporting_evidence]
            }
            recomputed_leaf_hashes.append(self._hash_leaf(leaf_dict))

        recomputed_root = self._compute_merkle_root(recomputed_leaf_hashes)
        return recomputed_root == cert.merkle_root

    def _hash_leaf(self, data: Dict[str, Any]) -> str:
        canonical_json = json.dumps(data, sort_keys=True)
        return hashlib.sha256((self.salt + canonical_json).encode("utf-8")).hexdigest()

    def _compute_merkle_root(self, hashes: List[str]) -> str:
        if not hashes:
            return hashlib.sha256(b"empty").hexdigest()
        if len(hashes) == 1:
            return hashes[0]

        current_level = list(hashes)
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                h1 = current_level[i]
                h2 = current_level[i + 1] if i + 1 < len(current_level) else h1
                combined = hashlib.sha256((h1 + h2).encode("utf-8")).hexdigest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0]
