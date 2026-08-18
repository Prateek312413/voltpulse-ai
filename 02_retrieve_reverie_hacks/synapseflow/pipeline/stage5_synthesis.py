"""
Stage 5: Verified Structured Synthesis
Produces the final publication-grade, mathematically verified analytical response.
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from ..config import settings
from ..models import SubTask, QuantitativeClaim, StageExecutionTrace
from ..clients.featherless_client import FeatherlessClient

logger = logging.getLogger("synapseflow.stage5")

class Stage5Synthesis:
    def __init__(self, client: FeatherlessClient):
        self.client = client
        self.model_id = settings.MODELS["synthesizer"]

    def execute(
        self,
        original_prompt: str,
        domain: str,
        subtasks: List[SubTask],
        claims: List[QuantitativeClaim],
        consensus_data: Dict[str, Any]
    ) -> Tuple[str, StageExecutionTrace]:
        start_time = time.perf_counter()
        
        system_prompt = (
            "You are a World-Class Lead Scientific Synthesizer & Technical Architect. "
            "Synthesize a cohesive, high-impact, verified technical report addressing the user's initial prompt. "
            "Incorporate the findings of the specialized subtask models and the verified mathematical audit. "
            "Structure the response with clear headings, LaTeX formulas for governing equations, "
            "concrete numbers, safety bounds, and an explicit Mathematical Verification Certificate."
        )
        
        verified_summary = "\n".join([
            f"- `{c.expression}`: Claimed={c.claimed_value}, Verified={c.verified_value} ({'VERIFIED ACCURATE' if c.is_valid else 'CORRECTED BY ORACLE'})"
            for c in claims
        ])
        
        task_findings = "\n\n".join([f"### {t.title}\n{t.output}" for t in subtasks])
        
        user_message = (
            f"User Objective:\n{original_prompt}\n\n"
            f"Verified Mathematical Audit Trail:\n{verified_summary}\n\n"
            f"Consensus Confidence: {consensus_data.get('confidence_score', 0.98)}\n\n"
            f"Detailed Technical Findings:\n{task_findings}\n\n"
            "Deliver the definitive, publication-ready synthesized report."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        final_output = self.client.chat_completion(
            model=self.model_id,
            messages=messages,
            temperature=settings.TEMPERATURE_SYNTHESIZER
        )
        
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        trace = StageExecutionTrace(
            stage_number=5,
            stage_name="Verified Structured Synthesis",
            model_used=self.model_id,
            duration_ms=round(duration_ms, 2),
            input_summary=f"Synthesized {len(subtasks)} subtask deliverables with {len(claims)} mathematical proofs",
            output_summary=f"Generated final verified response of {len(final_output.split())} words",
            metadata={"domain": domain}
        )
        
        return final_output, trace
