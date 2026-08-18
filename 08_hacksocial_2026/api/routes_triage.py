"""
ResilioNet AI - Crisis Triage & SOS Intake Endpoints
"""

import time
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
try:
    from core.state import crisis_db
    from core.crisis_triage_nlp import TriageResult
    from core.resource_optimizer import DemandRequest
except ImportError:
    from ..core.state import crisis_db
    from ..core.crisis_triage_nlp import TriageResult
    from ..core.resource_optimizer import DemandRequest

router = APIRouter()


class SOSSubmissionRequest(BaseModel):
    message_text: str = Field(..., min_length=3, description="Distress message / SOS transcript")
    sender_name: Optional[str] = "Anonymous Citizen"
    zone_id: Optional[str] = "ZONE-DEFAULT"
    override_lat: Optional[float] = None
    override_lon: Optional[float] = None
    contact_phone: Optional[str] = None


class BatchTriageRequest(BaseModel):
    messages: List[str]


@router.get("/list", response_model=List[TriageResult])
async def list_triage_records(limit: int = 50, min_urgency: float = 0.0):
    """Fetches list of parsed distress triage records sorted by urgency."""
    records = [
        t for t in crisis_db.triage_records.values()
        if t.urgency_score >= min_urgency
    ]
    return sorted(records, key=lambda x: x.urgency_score, reverse=True)[:limit]


@router.get("/{triage_id}", response_model=TriageResult)
async def get_triage_record(triage_id: str):
    """Retrieves specific triage record by ID."""
    if triage_id not in crisis_db.triage_records:
        raise HTTPException(status_code=404, detail=f"Triage ID '{triage_id}' not found")
    return crisis_db.triage_records[triage_id]


@router.post("/submit_sos", response_model=TriageResult)
async def submit_sos(req: SOSSubmissionRequest):
    """
    Ingests live citizen SOS signal, executes instant NLP triage and entity parsing,
    adds demand node to live crisis grid, and triggers audit logging.
    """
    ts = time.time()
    req_id = f"SOS-LIVE-{int(ts * 1000) % 100000:05d}"

    triage = crisis_db.nlp_engine.analyze_message(req.message_text, triage_id=req_id)
    crisis_db.triage_records[req_id] = triage

    # Geocoding fallback
    lat = req.override_lat or triage.entities.latitude or 37.7749
    lon = req.override_lon or triage.entities.longitude or -122.4194

    req_items = {}
    if triage.entities.specific_supplies_needed:
        for s in triage.entities.specific_supplies_needed:
            req_items[s] = max(1, triage.entities.headcount)
    else:
        req_items["potable_water"] = max(2, triage.entities.headcount * 2)

    demand = DemandRequest(
        request_id=req_id,
        requester_name=req.sender_name or "Anonymous Citizen",
        latitude=lat,
        longitude=lon,
        urgency_score=triage.urgency_score,
        headcount=triage.entities.headcount,
        required_items=req_items,
        special_requirements=triage.entities.medical_conditions,
        zone_id=req.zone_id or "ZONE-DEFAULT",
        timestamp_created=ts
    )
    crisis_db.raw_demands[req_id] = demand

    # Append to cryptographic audit ledger
    crisis_db.audit_ledger.append_event("SOS_INGESTED_LIVE", {
        "request_id": req_id,
        "urgency_score": triage.urgency_score,
        "category": triage.primary_category.value,
        "headcount": triage.entities.headcount
    })

    # Auto-reoptimize network
    crisis_db.run_matching_cycle()

    return triage


@router.post("/parse_preview", response_model=TriageResult)
async def parse_preview(message_text: str):
    """Runs zero-persistence instant triage parser for operator live typing / audio mic preview."""
    return crisis_db.nlp_engine.analyze_message(message_text, triage_id="PREVIEW-001")


@router.post("/batch_triage", response_model=List[TriageResult])
async def batch_triage(req: BatchTriageRequest):
    """Processes bulk multi-channel social feed / emergency SMS messages in parallel."""
    results = []
    for i, msg in enumerate(req.messages):
        tid = f"BATCH-{i+1:03d}"
        res = crisis_db.nlp_engine.analyze_message(msg, triage_id=tid)
        results.append(res)
    return results
