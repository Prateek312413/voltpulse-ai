"""
Atomic Claim Decomposition Engine.
Splits compound statements into discrete, falsifiable, and predicate-structured atomic claims.
"""

import re
from typing import List, Tuple, Optional
from evidencemesh.models import AtomicClaim, ClaimType, VerificationStatus


class ClaimDecomposer:
    """
    Decomposes unstructured natural language statements, scientific abstracts,
    or technical claims into atomic proposition units with semantic roles.
    """

    def __init__(self):
        # Numerical regex for detecting statistical and quantitative claims
        self.num_pattern = re.compile(
            r'(\b\d+(?:\.\d+)?\s*(?:%|percent|mg|ml|km|kWh|Wh/kg|hours|days|fold|x|patients|tokens/sec|ms)?\b)',
            re.IGNORECASE
        )
        # Causal connectors
        self.causal_connectors = [
            "leads to", "causes", "results in", "reduces", "increases",
            "improves", "triggers", "decreases", "suppresses", "enhances"
        ]

    def decompose(self, text: str) -> List[AtomicClaim]:
        """
        Decomposes input text into atomic claims.
        """
        if not text or not text.strip():
            return []

        # Split sentences and compound conjunction clauses
        raw_sentences = self._split_sentences(text)
        claims: List[AtomicClaim] = []
        claim_counter = 1

        for sent in raw_sentences:
            sub_clauses = self._split_compound_clauses(sent)
            for clause in sub_clauses:
                clause = clause.strip()
                if len(clause) < 6:
                    continue

                claim_type = self._classify_claim_type(clause)
                subject, predicate, obj_val, num_val, unit = self._extract_semantic_roles(clause)

                claim = AtomicClaim(
                    claim_id=f"CLM-{claim_counter:03d}",
                    text=clause,
                    claim_type=claim_type,
                    subject=subject,
                    predicate=predicate,
                    object_value=obj_val,
                    numerical_value=num_val,
                    unit=unit,
                    status=VerificationStatus.UNCERTAIN,
                    confidence_score=0.5,
                    epistemic_uncertainty=0.5,
                    aleatoric_uncertainty=0.1
                )
                claims.append(claim)
                claim_counter += 1

        return claims

    def _split_sentences(self, text: str) -> List[str]:
        # Split on sentence terminators while preserving decimal numbers
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+'
        raw = re.split(pattern, text.strip())
        return [s.strip() for s in raw if s.strip()]

    def _split_compound_clauses(self, sentence: str) -> List[str]:
        # Split on coordinating conjunctions if they form separate assertions
        delimiters = [";", " whereas ", " while also ", " and consequently "]
        parts = [sentence]
        for delim in delimiters:
            new_parts = []
            for p in parts:
                if delim in p.lower():
                    splits = re.split(re.escape(delim), p, flags=re.IGNORECASE)
                    new_parts.extend([s.strip() for s in splits if s.strip()])
                else:
                    new_parts.append(p)
            parts = new_parts
        return parts

    def _classify_claim_type(self, clause: str) -> ClaimType:
        low = clause.lower()
        if any(conn in low for conn in self.causal_connectors):
            return ClaimType.CAUSAL_LINK
        if any(w in low for w in ["%", "percent", "p <", "ci ", "mg", "wh/kg", "ratio", "fold", "increased by"]):
            return ClaimType.STATISTICAL
        if any(w in low for w in ["will ", "projected to", "predict", "estimated to in 20"]):
            return ClaimType.PREDICTION
        if any(w in low for w in ["must", "should", "unethical", "best", "imperative"]):
            return ClaimType.NORMATIVE
        return ClaimType.ATOMIC_FACT

    def _extract_semantic_roles(self, clause: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float], Optional[str]]:
        # Extract numerical value and unit
        num_val = None
        unit = None
        num_match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)?', clause)
        if num_match:
            try:
                num_val = float(num_match.group(1))
                unit = num_match.group(2) if num_match.group(2) else None
            except ValueError:
                pass

        # Basic Subject - Predicate - Object extraction heuristic
        words = clause.split()
        if len(words) >= 3:
            subject = " ".join(words[:2])
            predicate = words[2]
            obj_val = " ".join(words[3:]) if len(words) > 3 else None
        else:
            subject = words[0] if words else None
            predicate = words[1] if len(words) > 1 else None
            obj_val = None

        return subject, predicate, obj_val, num_val, unit
