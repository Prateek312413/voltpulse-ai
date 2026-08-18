"""
AegisMed CockroachDB Model Context Protocol (MCP) Server
Enables AI Agents (Claude Code, Cursor, LangChain) to directly query and update
persistent agentic memory in CockroachDB via standard MCP protocol.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from aegismed.database.connection import get_db_session
from aegismed.memory import AgenticMemoryEngine
from aegismed.agents.orchestrator import SwarmOrchestrator

logger = logging.getLogger("aegismed.mcp")


class CockroachMCPServer:
    """Implements Model Context Protocol (MCP) endpoints for CockroachDB Agentic Memory."""

    def __init__(self):
        self.server_name = "aegismed-cockroachdb-mcp"
        self.version = "1.0.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns MCP tool definitions exposed to AI agents."""
        return [
            {
                "name": "cockroach_query_episodic_memory",
                "description": "Performs semantic vector similarity search against patient episodic memories in CockroachDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_uid": {"type": "string", "description": "Patient identifier"},
                        "query_text": {"type": "string", "description": "Clinical presentation or question to search"},
                        "top_k": {"type": "integer", "default": 3}
                    },
                    "required": ["patient_uid", "query_text"]
                }
            },
            {
                "name": "cockroach_check_contraindications",
                "description": "Queries CockroachDB Semantic Guidelines & patient history to detect dangerous drug-allergy interactions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_uid": {"type": "string", "description": "Patient identifier"},
                        "candidate_medications": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["patient_uid", "candidate_medications"]
                }
            },
            {
                "name": "cockroach_execute_clinical_swarm",
                "description": "Runs full 4-tier multi-agent clinical consultation with ACID state locking.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_uid": {"type": "string"},
                        "chief_complaint": {"type": "string"},
                        "symptoms": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["patient_uid", "chief_complaint"]
                }
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool invoked by an MCP client."""
        with get_db_session() as db:
            engine = AgenticMemoryEngine(db)

            if tool_name == "cockroach_query_episodic_memory":
                p_uid = arguments.get("patient_uid")
                query = arguments.get("query_text")
                top_k = arguments.get("top_k", 3)
                results = engine.episodic.recall_relevant_episodes(p_uid, query, top_k=top_k)
                return {"status": "SUCCESS", "results": results}

            elif tool_name == "cockroach_check_contraindications":
                p_uid = arguments.get("patient_uid")
                meds = arguments.get("candidate_medications", [])
                pharma = SwarmOrchestrator(db).pharma
                res = pharma.perform_safety_audit(f"mcp_sess_{p_uid}", p_uid, meds)
                return {"status": "SUCCESS", "safety_report": res}

            elif tool_name == "cockroach_execute_clinical_swarm":
                p_uid = arguments.get("patient_uid")
                cc = arguments.get("chief_complaint")
                sym = arguments.get("symptoms", [])
                orchestrator = SwarmOrchestrator(db)
                out = orchestrator.run_consultation_swarm(p_uid, cc, sym, {})
                return {"status": "SUCCESS", "consultation": out}

            else:
                return {"status": "ERROR", "message": f"Unknown tool '{tool_name}'"}


mcp_server = CockroachMCPServer()
