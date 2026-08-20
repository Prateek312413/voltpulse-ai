"""
Unit and Integration Tests for ProcurePulse FastAPI Server.
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db_connection

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_rfqs" in data
    assert "total_calls_placed" in data
    assert "total_savings_generated" in data


def test_list_rfqs_and_suppliers():
    rfqs_res = client.get("/api/rfqs")
    assert rfqs_res.status_code == 200
    assert len(rfqs_res.json()) >= 1

    suppliers_res = client.get("/api/suppliers")
    assert suppliers_res.status_code == 200
    assert len(suppliers_res.json()) >= 3


def test_create_rfq():
    payload = {
        "title": "API Test RFQ: Titanium Fasteners",
        "sku": "TI-FAST-M8",
        "description": "Grade 5 Titanium M8 Hex Bolts 35mm",
        "target_quantity": 100,
        "target_unit_budget": 12.50,
        "required_delivery_date": "2026-09-15",
        "urgency": "standard",
        "allow_substitutions": True,
    }
    response = client.post("/api/rfqs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "rfq_id" in data


def test_dispatch_and_compare_quotes():
    dispatch_payload = {
        "rfq_id": "RFQ-2026-8810",
        "supplier_ids": ["sup-apex", "sup-midwest"],
        "mode": "simulate",
    }
    disp_res = client.post("/api/calls/dispatch", json=dispatch_payload)
    assert disp_res.status_code == 200
    disp_data = disp_res.json()
    assert disp_data["ok"] is True
    assert disp_data["dispatched_count"] == 2

    comp_res = client.get("/api/quotes/compare/RFQ-2026-8810")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "bids" in comp_data


def test_generate_purchase_order():
    # Insert a seeded quote extraction into DB to guarantee presence for PO generation test
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO quote_extractions (
            id, call_run_id, rfq_id, supplier_id, representative_name, quote_ref, sku_quoted,
            is_exact_match, stock_status, lead_time_days, base_unit_price, total_cost,
            volume_tiers_json, freight_terms, estimated_freight, citations_json, notes
        )
        VALUES (
            'ext_test_01', 'run_test_01', 'RFQ-2026-8810', 'sup-apex', 'Sarah Miller', 'Q-88192-A',
            'SS-400-1-4', 1, 'in_stock', 2, 42.50, 10625.00, '[]', 'FOB Destination', 0.0, '[]', 'Test quote'
        )
        """
    )
    conn.commit()
    conn.close()

    po_payload = {
        "rfq_id": "RFQ-2026-8810",
        "supplier_id": "sup-apex",
        "approved_by": "Alex Morgan (Procurement Lead)",
    }
    po_res = client.post("/api/po/generate", json=po_payload)
    assert po_res.status_code == 200
    po_data = po_res.json()
    assert po_data["ok"] is True
    assert "po_number" in po_data
    assert po_data["erp_synced"] is True
