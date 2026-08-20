"""
Database Layer for ProcurePulse AI
Stores RFQ campaigns, supplier records, call runs, structured quote extractions, and purchase orders.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "procurepulse.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema and seeds initial industrial suppliers and demo RFQs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Suppliers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        region TEXT DEFAULT 'US-Central',
        category TEXT DEFAULT 'Industrial Valves & Fasteners',
        rating REAL DEFAULT 4.5,
        total_orders_completed INTEGER DEFAULT 12,
        is_preferred INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. RFQ Campaigns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rfq_campaigns (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        sku TEXT NOT NULL,
        description TEXT NOT NULL,
        target_quantity INTEGER NOT NULL,
        target_unit_budget REAL NOT NULL,
        required_delivery_date TEXT,
        urgency TEXT DEFAULT 'standard',
        allow_substitutions INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active', -- draft, active, evaluating, completed
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Call Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_runs (
        id TEXT PRIMARY KEY,
        rfq_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        mode TEXT DEFAULT 'simulate', -- live, simulate
        plan_id TEXT,
        run_id TEXT,
        confirm_token TEXT,
        status TEXT DEFAULT 'pending', -- pending, planning, in_progress, completed, failed
        disposition TEXT DEFAULT 'unknown',
        duration_seconds INTEGER DEFAULT 0,
        transcript TEXT,
        started_at TEXT,
        completed_at TEXT,
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rfq_id) REFERENCES rfq_campaigns(id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )
    """)

    # 4. Quote Extractions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quote_extractions (
        id TEXT PRIMARY KEY,
        call_run_id TEXT NOT NULL,
        rfq_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        representative_name TEXT,
        quote_ref TEXT,
        sku_quoted TEXT NOT NULL,
        is_exact_match INTEGER DEFAULT 1,
        stock_status TEXT DEFAULT 'in_stock',
        lead_time_days INTEGER DEFAULT 2,
        base_unit_price REAL NOT NULL,
        total_cost REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        volume_tiers_json TEXT DEFAULT '[]',
        freight_terms TEXT,
        estimated_freight REAL DEFAULT 0.0,
        substitute_json TEXT,
        mcda_score REAL DEFAULT 0.0,
        rank INTEGER DEFAULT 1,
        is_recommended INTEGER DEFAULT 0,
        confidence_score REAL DEFAULT 0.95,
        citations_json TEXT DEFAULT '[]',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (call_run_id) REFERENCES call_runs(id),
        FOREIGN KEY (rfq_id) REFERENCES rfq_campaigns(id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )
    """)

    # 5. Purchase Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        id TEXT PRIMARY KEY,
        po_number TEXT NOT NULL UNIQUE,
        rfq_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        quote_extraction_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        freight_amount REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        lead_time_days INTEGER NOT NULL,
        status TEXT DEFAULT 'issued', -- drafted, issued, acknowledged, fulfilled
        approved_by TEXT NOT NULL,
        notes TEXT,
        erp_synced INTEGER DEFAULT 1,
        erp_sync_payload TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rfq_id) REFERENCES rfq_campaigns(id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )
    """)

    # Seed Initial Suppliers if empty
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] == 0:
        seed_suppliers = [
            (
                "sup-apex",
                "Apex Industrial Fasteners & Valves",
                "+18005550199",
                "sales@apexindustrial.com",
                "US-South (Dallas, TX)",
                "Industrial Valves & Fasteners",
                4.8,
                48,
                1,
            ),
            (
                "sup-midwest",
                "Midwest Fluid Controls",
                "+18005550188",
                "quotes@midwestfluid.com",
                "US-Midwest (Chicago, IL)",
                "Pneumatics & High-Pressure Valves",
                4.9,
                82,
                1,
            ),
            (
                "sup-titan",
                "Titan Bearing & Hardware Co.",
                "+18005550177",
                "orders@titanbearing.com",
                "US-East (Cleveland, OH)",
                "Bearings & Heavy Mechanicals",
                4.6,
                35,
                1,
            ),
            (
                "sup-precision",
                "Precision Metals & Component Direct",
                "+18005550166",
                "commercial@precisionmetalsdirect.com",
                "US-West (Denver, CO)",
                "Custom Alloy & Spec Hardware",
                4.7,
                29,
                1,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO suppliers (id, name, phone, email, region, category, rating, total_orders_completed, is_preferred)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_suppliers,
        )

    # Seed Initial Demo RFQ if empty
    cursor.execute("SELECT COUNT(*) FROM rfq_campaigns")
    if cursor.fetchone()[0] == 0:
        seed_rfqs = [
            (
                "RFQ-2026-8810",
                "Emergency Refurbishment: 316SS Ball Valves (250 units)",
                "SS-400-1-4",
                "1/4 in. 316 Stainless Steel High Pressure Ball Valve, 1000 PSI, NPT Female",
                250,
                45.00,
                "2026-09-05",
                "expedited",
                1,
                "active",
            ),
            (
                "RFQ-2026-8811",
                "Turbine Overhaul: Deep Groove Ceramic Bearings (100 units)",
                "6208-2RS-C3",
                "Deep Groove Ball Bearing 40x80x18mm, Rubber Seals, C3 Clearance",
                100,
                38.50,
                "2026-09-12",
                "standard",
                1,
                "active",
            ),
            (
                "RFQ-2026-8812",
                "Hydraulic Power Unit: Flange O-Ring Kits (500 units)",
                "VITON-AS568-214",
                "Fluoropolymer Viton Elastomer O-Ring Seal, 75 Durometer, High Temp",
                500,
                4.20,
                "2026-09-02",
                "standard",
                1,
                "active",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO rfq_campaigns (id, title, sku, description, target_quantity, target_unit_budget, required_delivery_date, urgency, allow_substitutions, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_rfqs,
        )

    conn.commit()
    conn.close()


# Ensure DB is initialized on module import
init_db()
