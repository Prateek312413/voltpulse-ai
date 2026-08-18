"""
Unit Tests for Offline Mesh Protocol & Disaster Blockchain Ledger
"""

import pytest
from core.mesh_packet_crypto import MeshPacketEngine, DisasterAuditLedger


@pytest.fixture
def mesh_engine():
    return MeshPacketEngine(node_id="NODE-TEST-01")


@pytest.fixture
def ledger():
    return DisasterAuditLedger(node_id="NODE-TEST-01")


def test_packet_creation_and_hmac_verification(mesh_engine):
    payload = {"sos_id": "REQ-100", "urgency": 9.5, "headcount": 4}
    packet = mesh_engine.create_packet("SOS_BEACON", payload)

    assert packet.is_verified is True
    assert len(packet.signature_hmac) == 64

    # Another engine with same key should verify packet
    peer_engine = MeshPacketEngine(node_id="NODE-PEER-02")
    is_valid, msg = peer_engine.verify_and_ingest_packet(packet)
    assert is_valid is True
    assert msg == "PACKET_VERIFIED_AND_ACCEPTED"


def test_tampered_packet_rejection(mesh_engine):
    payload = {"sos_id": "REQ-100", "urgency": 9.5}
    packet = mesh_engine.create_packet("SOS_BEACON", payload)

    # Tamper with payload
    packet.payload_data["urgency"] = 1.0

    peer_engine = MeshPacketEngine(node_id="NODE-PEER-02")
    is_valid, msg = peer_engine.verify_and_ingest_packet(packet)
    assert is_valid is False
    assert "TAMPER_DETECTED" in msg


def test_ledger_chain_and_verification(ledger):
    ledger.append_event("SOS_INGESTED", {"req": "REQ-01", "urgency": 8.0})
    ledger.append_event("ALLOCATION_MATCHED", {"match": "M-01", "hub": "HUB-CENTRAL"})
    ledger.append_event("AID_DELIVERED", {"match": "M-01", "status": "DELIVERED"})

    assert len(ledger.chain) == 4  # Genesis + 3 events
    is_intact, report = ledger.verify_chain_integrity()
    assert is_intact is True
    assert report == "LEDGER_INTEGRITY_VERIFIED"


def test_ledger_tampering_detection(ledger):
    ledger.append_event("TRANSACTION_A", {"amount": 50})
    ledger.append_event("TRANSACTION_B", {"amount": 100})

    # Artificially modify event payload in block 1
    ledger.chain[1].event_payload["amount"] = 99999

    is_intact, report = ledger.verify_chain_integrity()
    assert is_intact is False
    assert "Tampered block detected" in report
