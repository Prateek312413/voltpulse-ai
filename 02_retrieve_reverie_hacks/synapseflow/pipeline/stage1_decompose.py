"""
Stage 1: Intent Classification & Subtask Decomposition
Uses Mistral-Nemo-Instruct on Featherless to break down complex scientific/engineering prompts.
"""

import json
import logging
import time
from typing import List, Dict, Any, Tuple
from ..config import settings
from ..models import SubTask, StageExecutionTrace
from ..clients.featherless_client import FeatherlessClient

logger = logging.getLogger("synapseflow.stage1")

class Stage1Decomposition:
    def __init__(self, client: FeatherlessClient):
        self.client = client
        self.model_id = settings.MODELS["router"]

    def execute(self, prompt: str, domain: str) -> Tuple[List[SubTask], StageExecutionTrace]:
        start_time = time.perf_counter()
        
        system_prompt = (
            "You are an expert Scientific & Engineering Workflow Architect. "
            "Your task is to decompose the user's complex technical prompt into 2 to 4 granular, sequential subtasks. "
            "For each subtask, specify: 'id', 'title', 'description', 'assigned_model_role' ('reasoner', 'coder'), "
            "and 'requires_symbolic_verification' (true if it contains math, thermodynamics, kinetics, or data calculations). "
            "Output strictly valid JSON with key 'subtasks'."
        )
        
        user_message = f"Domain: {domain}\nComplex Technical Prompt:\n{prompt}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        raw_output = self.client.chat_completion(
            model=self.model_id,
            messages=messages,
            temperature=settings.TEMPERATURE_ROUTER,
            response_format={"type": "json_object"}
        )
        
        subtasks: List[SubTask] = []
        try:
            parsed = json.loads(raw_output)
            tasks_data = parsed.get("subtasks", [])
            for t in tasks_data:
                role = t.get("assigned_model_role", "reasoner")
                assigned_model = settings.MODELS.get(role, settings.MODELS["reasoner"])
                subtasks.append(SubTask(
                    id=t.get("id", f"task_{len(subtasks)+1}"),
                    title=t.get("title", "Analytical Step"),
                    description=t.get("description", ""),
                    assigned_model_role=role,
                    assigned_model_id=assigned_model,
                    requires_symbolic_verification=bool(t.get("requires_symbolic_verification", False)),
                    status="pending"
                ))
        except Exception as e:
            logger.warning(f"Failed to parse decomposition JSON: {e}. Generating default subtasks.")
            subtasks = [
                SubTask(
                    id="task_1",
                    title="Theoretical Formulation & State Equations",
                    description="Derive governing equations and mathematical parameters.",
                    assigned_model_role="reasoner",
                    assigned_model_id=settings.MODELS["reasoner"],
                    requires_symbolic_verification=True
                ),
                SubTask(
                    id="task_2",
                    title="Energy & Parameter Bounds Evaluation",
                    description="Evaluate quantitative values, heat loss, and rate metrics.",
                    assigned_model_role="reasoner",
                    assigned_model_id=settings.MODELS["reasoner"],
                    requires_symbolic_verification=True
                ),
                SubTask(
                    id="task_3",
                    title="Operating Envelope & Safety Constraints",
                    description="Generate structured JSON specification of bounds and thresholds.",
                    assigned_model_role="coder",
                    assigned_model_id=settings.MODELS["coder"],
                    requires_symbolic_verification=False
                )
            ]
            
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        trace = StageExecutionTrace(
            stage_number=1,
            stage_name="Intent & Task Decomposition",
            model_used=self.model_id,
            duration_ms=round(duration_ms, 2),
            input_summary=f"Decomposed prompt of {len(prompt)} chars in domain '{domain}'",
            output_summary=f"Generated {len(subtasks)} structured subtasks",
            metadata={"subtask_count": len(subtasks), "model_role": "router"}
        )
        
        return subtasks, trace
