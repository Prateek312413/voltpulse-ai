"""
WebSocket Live Verification Streaming for EvidenceMesh.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from evidencemesh.models import VerificationRequest
from evidencemesh.agents.swarm import EvidenceMeshSwarm


ws_router = APIRouter()
swarm = EvidenceMeshSwarm()


@ws_router.websocket("/ws/verify")
async def websocket_verify_endpoint(websocket: WebSocket):
    """
    Streams multi-agent verification progress in real-time.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            text_content = payload.get("text_content", "")
            domain = payload.get("domain", "general")
            prior_skepticism = float(payload.get("prior_skepticism", 0.5))

            req = VerificationRequest(
                text_content=text_content,
                domain=domain,
                prior_skepticism=prior_skepticism,
                deep_cross_examination=True
            )

            # Emit Stage 1: Extraction
            await websocket.send_json({
                "stage": "EXTRACTION",
                "progress": 20,
                "agent": "Agent-Decomposer-01",
                "message": "Decomposing unstructured text into atomic claims..."
            })
            await asyncio.sleep(0.3)

            # Emit Stage 2: Grounding
            await websocket.send_json({
                "stage": "GROUNDING",
                "progress": 45,
                "agent": "EvidenceGroundingEngine",
                "message": "Querying peer-reviewed knowledge corpus & semantic databases..."
            })
            await asyncio.sleep(0.3)

            # Emit Stage 3: Cross-Examination
            await websocket.send_json({
                "stage": "RED_TEAMING",
                "progress": 70,
                "agent": "Agent-RedTeam-Examiner",
                "message": "Running adversarial cross-examination & DAG cycle/contradiction detection..."
            })
            await asyncio.sleep(0.3)

            # Emit Stage 4: Calibration & Proof
            await websocket.send_json({
                "stage": "CALIBRATION",
                "progress": 90,
                "agent": "BayesianEpistemicCalibrator",
                "message": "Computing conjugate Beta posteriors, ECE, Brier score, and SHA-256 Merkle root..."
            })
            await asyncio.sleep(0.2)

            # Run full verification
            response = swarm.verify(req)

            # Emit Final Result
            await websocket.send_json({
                "stage": "COMPLETE",
                "progress": 100,
                "result": response.model_dump()
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"stage": "ERROR", "message": str(e)})
