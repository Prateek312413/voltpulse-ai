"""
Unit tests for EmergencySentinel
"""
import pytest
from core.emergency_sentinel import EmergencySentinel

@pytest.fixture
def sentinel():
    return EmergencySentinel()

def test_trigger_sos_alert(sentinel):
    incident = sentinel.trigger_sos_alert(
        trigger_source="TEST_SWITCH",
        message="Test alert"
    )
    assert incident["urgency"] == "CRITICAL"
    assert incident["alert_id"].startswith("SOS-")
    assert len(incident["dispatched_channels"]) > 0
    assert len(sentinel.incident_history) == 1

def test_acknowledge_incident(sentinel):
    incident = sentinel.trigger_sos_alert()
    alert_id = incident["alert_id"]
    
    ack = sentinel.acknowledge_incident(alert_id, responder_name="Dr. Test")
    assert ack["acknowledgment_status"] == "RESOLVED"
    assert ack["resolved_by"] == "Dr. Test"
