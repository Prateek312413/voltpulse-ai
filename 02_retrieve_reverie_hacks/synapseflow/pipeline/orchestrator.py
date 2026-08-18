"""
Master Pipeline Orchestrator
Coordinates Stages 1 to 5 into an end-to-end deterministic multi-LLM workflow DAG.
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..models import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    StageExecutionTrace,
    QuantitativeClaim,
    SubTask
)
from ..clients.featherless_client import FeatherlessClient
from ..clients.wolfram_client import WolframClient
from .stage1_decompose import Stage1Decomposition
from .stage2_reason import Stage2Reasoning
from .stage3_verify import Stage3Verification
from .stage4_consensus import Stage4Consensus
from .stage5_synthesis import Stage5Synthesis

logger = logging.getLogger("synapseflow.orchestrator")

class PipelineOrchestrator:
    def __init__(
        self,
        featherless_client: Optional[FeatherlessClient] = None,
        wolfram_client: Optional[WolframClient] = None
    ):
        self.featherless = featherless_client or FeatherlessClient()
        self.wolfram = wolfram_client or WolframClient()
        
        self.stage1 = Stage1Decomposition(self.featherless)
        self.stage2 = Stage2Reasoning(self.featherless)
        self.stage3 = Stage3Verification(self.wolfram)
        self.stage4 = Stage4Consensus(self.featherless)
        self.stage5 = Stage5Synthesis(self.featherless)

    def run(self, request: PipelineExecutionRequest) -> PipelineExecutionResponse:
        """Executes the full 5-stage SynapseFlow prompt workflow."""
        pipeline_id = f"flow_{uuid.uuid4().hex[:8]}"
        overall_start = time.perf_counter()
        traces: List[StageExecutionTrace] = []
        
        logger.info(f"Starting SynapseFlow pipeline [{pipeline_id}] for prompt: '{request.prompt[:60]}...'")
        
        # Stage 1: Intent & Subtask Decomposition (Mistral-Nemo)
        subtasks, trace1 = self.stage1.execute(request.prompt, request.domain or "general_scientific")
        traces.append(trace1)
        
        # Stage 2: Multi-Model Parallel Reasoning (DeepSeek-V3 + Qwen-2.5-Coder)
        subtasks, trace2 = self.stage2.execute(subtasks, request.prompt)
        traces.append(trace2)
        
        # Stage 3: Symbolic Verification & Constraint Checker (Wolfram / SymPy)
        claims, hallucination_detected, hallucination_count, trace3 = self.stage3.execute(subtasks)
        traces.append(trace3)
        
        # Stage 4: Consensus & Cross-Model Debate (Kimi-K2.5 / GLM-5)
        consensus_data, trace4 = self.stage4.execute(subtasks, claims, request.prompt)
        traces.append(trace4)
        
        # Stage 5: Verified Structured Synthesis (DeepSeek-V3 / Kimi)
        final_output, trace5 = self.stage5.execute(
            request.prompt,
            request.domain or "general_scientific",
            subtasks,
            claims,
            consensus_data
        )
        traces.append(trace5)
        
        total_latency_ms = (time.perf_counter() - overall_start) * 1000.0
        confidence = float(consensus_data.get("confidence_score", 0.98))
        if hallucination_count > 0 and not request.strict_verification:
            confidence = max(0.60, confidence - (0.15 * hallucination_count))
            
        estimated_tokens = sum([len(t.output.split()) * 2 for t in subtasks if t.output]) + len(final_output.split()) * 2
        
        response = PipelineExecutionResponse(
            pipeline_id=pipeline_id,
            timestamp=datetime.utcnow().isoformat(),
            input_prompt=request.prompt,
            domain=request.domain or "general_scientific",
            final_output=final_output,
            confidence_score=round(confidence, 3),
            hallucination_detected=hallucination_detected,
            hallucination_count=hallucination_count,
            verified_claims=claims,
            subtasks=subtasks,
            stage_traces=traces,
            total_latency_ms=round(total_latency_ms, 2),
            token_usage_estimate=estimated_tokens
        )
        
        logger.info(f"Pipeline [{pipeline_id}] completed successfully in {total_latency_ms:.2f}ms (Confidence: {confidence*100:.1f}%)")
        return response
