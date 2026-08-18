"""
Emergency Sentinel Module for NeuroAccess AI.
Automated SOS detection, Caregiver dispatching, and Telemetry Audit Trail.
"""
from typing import Dict, List, Any
import datetime
import uuid

class EmergencySentinel:
    """
    Manages critical life-safety alerts, caregiver webhooks, and historical incident logging.
    """

    def __init__(self):
        self.incident_history: List[Dict[str, Any]] = []
        self.emergency_contacts = [
            {"name": "Primary Nurse Station", "channel": "TELEPHONY / VOIP", "phone": "+1-800-555-0199", "status": "ACTIVE"},
            {"name": "Attending Physician (Dr. Sarah Chen)", "channel": "PAGER / SMS", "phone": "+1-800-555-0214", "status": "ACTIVE"},
            {"name": "Emergency Family Guardian", "channel": "PUSH NOTIFICATION", "phone": "+1-800-555-0842", "status": "STANDBY"}
        ]

    def trigger_sos_alert(
        self, 
        trigger_source: str = "MANUAL_AAC_SWITCH", 
        message: str = "EMERGENCY: Immediate caregiver assistance required!",
        patient_id: str = "PT-8042-NEURO",
        location: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Creates a high-priority incident record and simulates dispatch across multi-channel alerting tiers.
        """
        alert_id = f"SOS-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        geo_location = location or {
            "facility": "General Hospital Rehabilitation Wing",
            "room": "Room 402B - Bed 1",
            "latitude": 37.7749,
            "longitude": -122.4194
        }

        incident = {
            "alert_id": alert_id,
            "patient_id": patient_id,
            "timestamp": timestamp,
            "trigger_source": trigger_source,
            "message": message,
            "location": geo_location,
            "urgency": "CRITICAL",
            "dispatched_channels": [c["name"] for c in self.emergency_contacts],
            "acknowledgment_status": "PENDING_ACK",
            "response_time_ms": 142
        }

        self.incident_history.insert(0, incident)
        return incident

    def get_incident_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent incident history."""
        return self.incident_history[:limit]

    def acknowledge_incident(self, alert_id: str, responder_name: str = "Nurse Sarah Jenkins") -> Dict[str, Any]:
        """Marks an alert as acknowledged and handled."""
        for inc in self.incident_history:
            if inc["alert_id"] == alert_id:
                inc["acknowledgment_status"] = "RESOLVED"
                inc["resolved_by"] = responder_name
                inc["resolved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                return inc
        return {"status": "NOT_FOUND", "alert_id": alert_id}
