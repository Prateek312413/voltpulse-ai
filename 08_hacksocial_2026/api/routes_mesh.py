"""
ResilioNet AI - Offline Mesh Protocol & Cryptographic Audit Ledger Endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
try:
    from core.state import crisis_db
    from core.mesh_packet_crypto import MeshPacket, LedgerBlock
except ImportError:
    from ..core.state import crisis_db
    from ..core.mesh_packet_crypto import MeshPacket, LedgerBlock

router = APIRouter()


class BroadcastPacketRequest(BaseModel):
    payload_type: str = Field(..., description="SOS_BEACON, TRIAGE_UPDATE, RESOURCE_ALLOCATION, DEPOT_STATUS")
    payload_data: Dict[str, Any]
    max_hops: int = 7


@router.get("/packets", response_model=List[MeshPacket])
async def list_mesh_packets(limit: int = 50):
    """Retrieves recent mesh packets exchanged on the local peer-to-peer radio grid."""
    return crisis_db.mesh_packets[-limit:]


@router.post("/broadcast", response_model=MeshPacket)
async def broadcast_packet(req: BroadcastPacketRequest):
    """Generates an HMAC-SHA256 digitally signed mesh packet for peer transmission."""
    packet = crisis_db.mesh_engine.create_packet(
        payload_type=req.payload_type,
        data=req.payload_data,
        max_hops=req.max_hops
    )
    crisis_db.mesh_packets.append(packet)

    crisis_db.audit_ledger.append_event("MESH_PACKET_BROADCAST", {
        "packet_id": packet.packet_id,
        "type": packet.payload_type,
        "sender": packet.sender_node_id
    })

    return packet


@router.post("/ingest_peer_packet")
async def ingest_peer_packet(packet: MeshPacket):
    """
    Ingests an incoming packet from a field peer mesh node.
    Verifies HMAC digital signature against tampering and checks hop-count limit.
    """
    is_valid, msg = crisis_db.mesh_engine.verify_and_ingest_packet(packet)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Packet rejected: {msg}")

    crisis_db.mesh_packets.append(packet)

    crisis_db.audit_ledger.append_event("MESH_PACKET_RECEIVED", {
        "packet_id": packet.packet_id,
        "sender": packet.sender_node_id,
        "type": packet.payload_type
    })

    return {"status": "ACCEPTED", "message": msg, "packet_id": packet.packet_id}


@router.get("/ledger/blocks", response_model=List[LedgerBlock])
async def get_ledger_blocks():
    """Returns the immutable disaster relief audit blockchain ledger."""
    return crisis_db.audit_ledger.chain


@router.get("/ledger/verify")
async def verify_ledger_integrity():
    """
    Performs full SHA-256 cryptographic verification across all chained blocks.
    Guarantees no aid fraud, record deletion, or unauthorized modifications.
    """
    is_valid, report = crisis_db.audit_ledger.verify_chain_integrity()
    return {
        "is_intact": is_valid,
        "total_blocks": len(crisis_db.audit_ledger.chain),
        "latest_block_hash": crisis_db.audit_ledger.chain[-1].block_hash if crisis_db.audit_ledger.chain else None,
        "report": report
    }
