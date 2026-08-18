"""
ResilioNet AI - Autonomous Situational Incident Commander Agent
Continuously analyzes disaster signals, detects logistics bottlenecks,
predicts supply burn-out windows, and generates actionable field directives.
"""

import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .crisis_triage_nlp import TriageResult
from .resource_optimizer import SupplyHub, DemandRequest, AllocationPlan
from .vulnerability_index import HyperlocalVulnerabilityIndex


class OperationalDirective(BaseModel):
    directive_id: str
    severity: str  # CRITICAL, HIGH_PRIORITY, ADVISORY
    category: str  # REALLOCATION, EVACUATION, LIFE_SAFETY, DEPOT_STOCKING
    title: str
    description: str
    recommended_action: str
    affected_zones: List[str]
    target_depots: List[str]
    timestamp: float


class SituationalAssessment(BaseModel):
    assessment_id: str
    timestamp: float
    overall_crisis_status: str  # RED_ESCALATION, AMBER_ACTIVE_RESPONSE, YELLOW_MONITORED, GREEN_STABILIZING
    total_active_sos: int
    unaddressed_critical_sos: int
    average_network_urgency: float
    equity_gini_score: float
    most_vulnerable_zones: List[str]
    critical_supply_shortages: List[str]
    depot_burnout_warnings: List[str]
    actionable_directives: List[OperationalDirective]
    executive_briefing_markdown: str


class SituationalIncidentCommander:
    """
    AI Incident Commander synthesizing data streams into high-level operational clarity.
    """

    def generate_assessment(
        self,
        triage_records: List[TriageResult],
        hubs: List[SupplyHub],
        zone_indexes: List[HyperlocalVulnerabilityIndex],
        latest_allocation_plan: Optional[AllocationPlan] = None
    ) -> SituationalAssessment:
        ts = time.time()
        aid = f"SITREP-{int(ts)}"

        total_sos = len(triage_records)
        critical_sos = sum(1 for t in triage_records if t.urgency_score >= 8.5)
        avg_urgency = sum(t.urgency_score for t in triage_records) / max(1, total_sos)

        # 1. Determine Crisis Status
        if critical_sos > 5 or avg_urgency > 7.5:
            status = "RED_ESCALATION"
        elif total_sos > 10 or avg_urgency > 5.5:
            status = "AMBER_ACTIVE_RESPONSE"
        elif total_sos > 0:
            status = "YELLOW_MONITORED"
        else:
            status = "GREEN_STABILIZING"

        # 2. Check Vulnerable Zones
        vulnerable_zones = [
            f"{z.zone_name} ({z.zone_id}) - HRVI {z.composite_hrvi} [{z.risk_tier}]"
            for z in sorted(zone_indexes, key=lambda x: x.composite_hrvi, reverse=True)
            if z.composite_hrvi >= 0.50
        ]

        # 3. Supply Depletion & Burnout Warnings
        depot_warnings = []
        supply_shortages = []
        for hub in hubs:
            if hub.operational_status == "OFFLINE":
                depot_warnings.append(f"Depot {hub.name} ({hub.hub_id}) is OFFLINE - routes disrupted")
                continue

            total_items = sum(it.quantity for it in hub.inventory.values())
            if total_items < 50:
                depot_warnings.append(f"CRITICAL DEPLETION: {hub.name} has only {total_items} items left in stock")

            for item_code, item in hub.inventory.items():
                if item.quantity <= 5:
                    supply_shortages.append(f"{item.name} at {hub.name} ({item.quantity} {item.unit} remaining)")

        # 4. Generate Dynamic Operational Directives
        directives: List[OperationalDirective] = []
        directive_counter = 1

        # Directive for high-urgency untriaged requests
        if critical_sos > 0:
            directives.append(OperationalDirective(
                directive_id=f"DIR-{directive_counter:03d}",
                severity="CRITICAL",
                category="LIFE_SAFETY",
                title=f"Immediate Dispatch to {critical_sos} Life-Threatening SOS Locations",
                description=f"There are {critical_sos} incoming calls with Urgency >= 8.5 involving active traps or critical medical distress.",
                recommended_action="Mobilize high-clearance swiftwater/SAR assets and prioritize trauma EMT units.",
                affected_zones=[z.zone_id for z in zone_indexes[:2]],
                target_depots=[h.hub_id for h in hubs if h.operational_status == "ACTIVE"][:2],
                timestamp=ts
            ))
            directive_counter += 1

        # Directive for High HRVI zones
        high_hrvi_zones = [z for z in zone_indexes if z.composite_hrvi >= 0.70]
        if high_hrvi_zones:
            zone_names = ", ".join(z.zone_name for z in high_hrvi_zones)
            directives.append(OperationalDirective(
                directive_id=f"DIR-{directive_counter:03d}",
                severity="HIGH_PRIORITY",
                category="REALLOCATION",
                title=f"Preemptive Supply Corridor to High-Risk Zones: {zone_names}",
                description=f"Vulnerability scoring indicates high infant/elderly ratios combined with grid/road failure in {zone_names}.",
                recommended_action="Transfer emergency battery generators, potable water tanks, and pediatric milk rations immediately.",
                affected_zones=[z.zone_id for z in high_hrvi_zones],
                target_depots=[h.hub_id for h in hubs if h.operational_status == "ACTIVE"][:2],
                timestamp=ts
            ))
            directive_counter += 1

        # Directive for Gini Inequality if allocation plan shows imbalance
        gini_score = latest_allocation_plan.gini_equity_index if latest_allocation_plan else 0.0
        if gini_score > 0.40:
            directives.append(OperationalDirective(
                directive_id=f"DIR-{directive_counter:03d}",
                severity="HIGH_PRIORITY",
                category="EQUITY_BALANCING",
                title="Geographic Supply Equity Disparity Alert",
                description=f"Current allocation Gini index is {gini_score} (above acceptable 0.35 threshold). Peripheral zones are experiencing supply starvation.",
                recommended_action="Enforce quota allocations for remote sectors and mobilize auxiliary volunteer transport fleets.",
                affected_zones=[z.zone_id for z in zone_indexes[-2:]],
                target_depots=[h.hub_id for h in hubs if h.operational_status == "ACTIVE"],
                timestamp=ts
            ))
            directive_counter += 1

        # 5. Executive Briefing Markdown
        briefing = self._compose_executive_briefing(
            status, total_sos, critical_sos, avg_urgency, gini_score, vulnerable_zones, directives
        )

        return SituationalAssessment(
            assessment_id=aid,
            timestamp=ts,
            overall_crisis_status=status,
            total_active_sos=total_sos,
            unaddressed_critical_sos=critical_sos,
            average_network_urgency=round(avg_urgency, 2),
            equity_gini_score=gini_score,
            most_vulnerable_zones=vulnerable_zones,
            critical_supply_shortages=supply_shortages[:8],
            depot_burnout_warnings=depot_warnings,
            actionable_directives=directives,
            executive_briefing_markdown=briefing
        )

    def _compose_executive_briefing(
        self,
        status: str,
        total_sos: int,
        critical_sos: int,
        avg_urgency: float,
        gini: float,
        vulnerable_zones: List[str],
        directives: List[OperationalDirective]
    ) -> str:
        lines = [
            f"# 🚨 ResilioNet Crisis Operations Situational Report",
            f"**Operational Status:** `{status}` &bull; **Average Network Urgency:** `{avg_urgency:.2f}/10.0`",
            "",
            "## 📊 Real-Time Crisis Telemetry",
            f"- **Active Distress Signals:** {total_sos} requests logged",
            f"- **Critical Life-Safety Threats:** {critical_sos} requests (Urgency $\\ge$ 8.5)",
            f"- **Resource Allocation Fairness (Gini Index):** `{gini:.3f}` *(0.00 = Optimal Equity)*",
            "",
            "## 📍 High-Risk Vulnerability Zones",
        ]
        if vulnerable_zones:
            for z in vulnerable_zones:
                lines.append(f"- **{z}**")
        else:
            lines.append("- All monitored zones currently within resilient thresholds.")

        lines.append("")
        lines.append("## ⚡ Priority Field Directives")
        if directives:
            for d in directives:
                lines.append(f"### [{d.severity}] {d.title}")
                lines.append(f"> **Action Required:** {d.recommended_action}")
                lines.append(f"*{d.description}*")
                lines.append("")
        else:
            lines.append("No critical emergency escalations pending.")

        return "\n".join(lines)
