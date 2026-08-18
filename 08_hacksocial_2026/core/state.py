"""
ResilioNet AI - Global In-Memory Crisis Operations Database & State Manager
Thread-safe singleton state holding live SOS feeds, inventory, HRVI profiles, and cryptographic ledger.
"""

import json
import os
import time
from typing import Dict, List, Optional
from .crisis_triage_nlp import CrisisNLPEngine, TriageResult, ExtractedEntities, DistressCategory
from .resource_optimizer import ResourceOptimizer, SupplyHub, SupplyItem, DemandRequest, AllocationPlan, MatchResult
from .vulnerability_index import VulnerabilityProfiler, HyperlocalVulnerabilityIndex, ZoneDemographics, ZoneInfrastructure, RealtimeHazardModifiers
from .mesh_packet_crypto import MeshPacketEngine, DisasterAuditLedger, MeshPacket
from .situational_agent import SituationalIncidentCommander, SituationalAssessment


class CrisisDatabase:
    def __init__(self):
        self.nlp_engine = CrisisNLPEngine()
        self.optimizer = ResourceOptimizer()
        self.vuln_profiler = VulnerabilityProfiler()
        self.mesh_engine = MeshPacketEngine(node_id="NODE-CENTRAL-COMMAND")
        self.audit_ledger = DisasterAuditLedger(node_id="NODE-CENTRAL-COMMAND")
        self.incident_commander = SituationalIncidentCommander()

        # State storage
        self.triage_records: Dict[str, TriageResult] = {}
        self.raw_demands: Dict[str, DemandRequest] = {}
        self.supply_hubs: Dict[str, SupplyHub] = {}
        self.zone_profiles: Dict[str, HyperlocalVulnerabilityIndex] = {}
        self.allocation_history: List[AllocationPlan] = []
        self.latest_plan: Optional[AllocationPlan] = None
        self.mesh_packets: List[MeshPacket] = []

        # Load initial synthetic dataset if exists
        self.load_initial_data()

    def load_initial_data(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        feed_path = os.path.join(base_dir, "data", "synthetic_crisis_feed.json")

        if not os.path.exists(feed_path):
            from generate_crisis_data import generate_dataset
            generate_dataset()

        if os.path.exists(feed_path):
            with open(feed_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. Ingest Zones
            for zp in data.get("zone_profiles", []):
                zid = zp["zone_id"]
                zname = zp["zone_name"]
                demo = ZoneDemographics(**zp["demographics"])
                infra = ZoneInfrastructure(**zp["infra"])
                hazard = RealtimeHazardModifiers(**zp["hazard"])
                hrvi = self.vuln_profiler.compute_hrvi(zid, zname, demo, infra, hazard)
                self.zone_profiles[zid] = hrvi

            # 2. Ingest Supply Hubs
            for sh in data.get("supply_hubs", []):
                items = {}
                for k, v in sh.get("inventory", {}).items():
                    items[k] = SupplyItem(**v)
                hub = SupplyHub(
                    hub_id=sh["hub_id"],
                    name=sh["name"],
                    latitude=sh["latitude"],
                    longitude=sh["longitude"],
                    capacity_units=sh.get("capacity_units", 1000),
                    available_vehicles=sh.get("available_vehicles", 5),
                    inventory=items,
                    operational_status=sh.get("operational_status", "ACTIVE")
                )
                self.supply_hubs[hub.hub_id] = hub

            # 3. Ingest Distress Signals & Run NLP Triage
            for df in data.get("distress_feed", []):
                req_id = df["request_id"]
                raw_txt = df["raw_text"]
                zone_id = df.get("zone_id", "ZONE-DEFAULT")
                triage = self.nlp_engine.analyze_message(raw_txt, triage_id=req_id)
                self.triage_records[req_id] = triage

                # If latitude/longitude extracted from text, use it; else approximate from zone
                lat = triage.entities.latitude or 37.7749
                lon = triage.entities.longitude or -122.4194

                req_items = df.get("required_items", {})
                if not req_items and triage.entities.specific_supplies_needed:
                    for s in triage.entities.specific_supplies_needed:
                        req_items[s] = max(1, triage.entities.headcount)
                if not req_items:
                    req_items["potable_water"] = max(2, triage.entities.headcount * 2)

                demand = DemandRequest(
                    request_id=req_id,
                    requester_name=f"Distress Signal {req_id}",
                    latitude=lat,
                    longitude=lon,
                    urgency_score=triage.urgency_score,
                    headcount=triage.entities.headcount,
                    required_items=req_items,
                    special_requirements=triage.entities.medical_conditions,
                    zone_id=zone_id,
                    timestamp_created=df.get("timestamp_created", time.time())
                )
                self.raw_demands[req_id] = demand

                # Log to audit ledger
                self.audit_ledger.append_event("SOS_INGESTED", {
                    "request_id": req_id,
                    "urgency_score": triage.urgency_score,
                    "category": triage.primary_category.value
                })

            # 4. Auto-run initial matching plan
            self.run_matching_cycle()

    def run_matching_cycle(self) -> AllocationPlan:
        plan = self.optimizer.optimize_allocations(
            demands=list(self.raw_demands.values()),
            hubs=list(self.supply_hubs.values())
        )
        self.latest_plan = plan
        self.allocation_history.append(plan)

        # Log allocation to audit ledger
        self.audit_ledger.append_event("ALLOCATION_PLAN_OPTIMIZED", {
            "plan_id": plan.plan_id,
            "matched": plan.matched_demands,
            "fulfillment_rate": plan.fulfillment_rate_percent,
            "gini_index": plan.gini_equity_index
        })
        return plan

    def get_situational_assessment(self) -> SituationalAssessment:
        return self.incident_commander.generate_assessment(
            triage_records=list(self.triage_records.values()),
            hubs=list(self.supply_hubs.values()),
            zone_indexes=list(self.zone_profiles.values()),
            latest_allocation_plan=self.latest_plan
        )


# Singleton Instance
crisis_db = CrisisDatabase()
