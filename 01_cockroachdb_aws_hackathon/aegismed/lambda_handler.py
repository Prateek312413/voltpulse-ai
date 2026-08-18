"""
AWS Lambda Serverless Entrypoint for AegisMed
Enables event-driven multi-agent clinical consultation workflows on AWS Lambda.
"""

import json
import logging
from aegismed.database.connection import init_db, get_db_session
from aegismed.agents.orchestrator import SwarmOrchestrator

logger = logging.getLogger("aegismed.lambda")

# Initialize database schema on cold start
init_db()


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint. Accepts API Gateway proxy events or direct invocation payloads.
    """
    try:
        body = event
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])

        patient_uid = body.get("patient_uid", "P-1001")
        chief_complaint = body.get("chief_complaint", "Routine checkup")
        symptoms = body.get("symptoms", [])
        vitals = body.get("vital_signs", {"bp_sys": 120, "bp_dia": 80, "hr": 72, "spo2": 98, "temp_c": 37.0})

        with get_db_session() as db:
            orchestrator = SwarmOrchestrator(db)
            result = orchestrator.run_consultation_swarm(
                patient_uid=patient_uid,
                chief_complaint=chief_complaint,
                symptoms=symptoms,
                vitals=vitals,
                save_as_episode=True
            )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Lambda execution error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
