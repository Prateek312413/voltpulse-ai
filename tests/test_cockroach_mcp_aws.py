"""
Tests for CockroachDB MCP Server and AWS Lambda Integration
"""

import pytest
import json
from aegismed.mcp.server import mcp_server
from aegismed.tools.ccloud_manager import ccloud_manager
from aegismed.providers.aws_s3 import s3_store
from aegismed.lambda_handler import lambda_handler
from aegismed.database.connection import init_db
from aegismed.database.seed_data import seed_all


@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    init_db()
    seed_all()


def test_mcp_server_tools_listing():
    tools = mcp_server.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "cockroach_query_episodic_memory" in tool_names
    assert "cockroach_check_contraindications" in tool_names
    assert "cockroach_execute_clinical_swarm" in tool_names


def test_mcp_episodic_query_execution():
    res = mcp_server.call_tool("cockroach_query_episodic_memory", {
        "patient_uid": "P-1001",
        "query_text": "Amoxicillin allergy rash",
        "top_k": 2
    })
    assert res["status"] == "SUCCESS"
    assert len(res["results"]) > 0


def test_ccloud_manager():
    status = ccloud_manager.get_cluster_status("aegismed-cluster")
    assert status["status"] == "HEALTHY"
    assert status["vector_indexing_enabled"] is True


def test_aws_s3_storage_provider():
    uri = s3_store.store_clinical_report("P-1001", "ep_test123", {"dx": "Pharyngitis"})
    assert "s3://aegismed-clinical-records/patients/P-1001/episodes/ep_test123.json" in uri


def test_aws_lambda_handler():
    event = {
        "patient_uid": "P-1001",
        "chief_complaint": "Acute throat soreness",
        "symptoms": ["Sore throat", "Fever"]
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "primary_diagnosis" in body
