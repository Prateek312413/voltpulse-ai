"""
Stage 2: Multi-Model Parallel Reasoning
Dispatches specialized subtasks across DeepSeek-V3 and Qwen-2.5-Coder on Featherless.ai.
"""

import logging
import time
from typing import List, Tuple
from ..config import settings
from ..models import SubTask, StageExecutionTrace
from ..clients.featherless_client import FeatherlessClient

logger = logging.getLogger("synapseflow.stage2")

class Stage2Reasoning:
    def __init__(self, client: FeatherlessClient):
        self.client = client

    def execute(self, subtasks: List[SubTask], original_prompt: str) -> Tuple[List[SubTask], StageExecutionTrace]:
        start_time = time.perf_counter()
        
        for task in subtasks:
            task.status = "running"
            model_id = task.assigned_model_id
            
            system_prompt = (
                f"You are a Principal Scientific AI Specialist executing '{task.title}'. "
                "Provide rigorous, step-by-step reasoning with explicit formulas and numerical substitutions. "
                "When stating calculations, format them as: 'EXPRESSION = INTERMEDIATE = RESULT'. "
                "Be strictly truthful, precise, and avoid unverified assumptions."
            )
            
            user_message = (
                f"Original Context: {original_prompt}\n\n"
                f"Subtask Instruction: {task.description}\n"
                "Please deliver your detailed analytical solution."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            output = self.client.chat_completion(
                model=model_id,
                messages=messages,
                temperature=settings.TEMPERATURE_REASONER
            )
            
            task.output = output
            task.reasoning_trace = [f"Executed on model {model_id}", f"Generated {len(output.split())} tokens"]
            task.status = "completed"
            
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        trace = StageExecutionTrace(
            stage_number=2,
            stage_name="Multi-Model Parallel Reasoning",
            model_used=f"{settings.MODELS['reasoner']} + {settings.MODELS['coder']}",
            duration_ms=round(duration_ms, 2),
            input_summary=f"Processed {len(subtasks)} subtasks across specialized model swarm",
            output_summary="Completed analytical derivations and structured schemas",
            metadata={"completed_tasks": [t.id for t in subtasks]}
        )
        
        return subtasks, trace
