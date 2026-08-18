"""
ResilioNet AI - Offline-First Cryptographic Mesh Protocol & Disaster Audit Ledger
Enables zero-connectivity peer-to-peer synchronization, HMAC-SHA256 digital signing,
and tamper-evident blockchain-style ledger auditing for humanitarian transparency.
"""

import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


class MeshPacket(BaseModel):
    packet_id: str
    sender_node_id: str
    timestamp: float
    hop_count: int = 0
    max_hops: int = 7
    payload_type: str  # SOS_BEACON, TRIAGE_UPDATE, RESOURCE_ALLOCATION, DEPOT_STATUS, LEDGER_BLOCK
    payload_data: Dict[str, Any]
    signature_hmac: str
    is_verified: bool = False


class LedgerBlock(BaseModel):
    block_index: int
    timestamp: float
    previous_hash: str
    event_type: str
    event_payload: Dict[str, Any]
    block_hash: str
    signer_node_id: str


class MeshPacketEngine:
    """
    Handles generation, signing, cryptographic verification, and hop-routing of mesh packets.
    """

    DEFAULT_SHARED_SECRET = "RESILIONET-HUMANITARIAN-COMMUNITY-KEY-2026"

    def __init__(self, node_id: str = "NODE-HUB-01", secret_key: Optional[str] = None):
        self.node_id = node_id
        self.secret_key = (secret_key or self.DEFAULT_SHARED_SECRET).encode('utf-8')
        self.seen_packet_ids: set = set()

    def create_packet(self, payload_type: str, data: Dict[str, Any], max_hops: int = 7) -> MeshPacket:
        """Constructs and cryptographically signs an outbound mesh packet."""
        ts = time.time()
        pid = f"PKT-{self.node_id}-{int(ts * 1000) % 10000000}-{abs(hash(json.dumps(data, sort_keys=True))) % 10000:04d}"

        # Canonical string for signature
        canonical_str = f"{pid}:{self.node_id}:{ts}:{payload_type}:{json.dumps(data, sort_keys=True)}"
        signature = hmac.new(self.secret_key, canonical_str.encode('utf-8'), hashlib.sha256).hexdigest()

        packet = MeshPacket(
            packet_id=pid,
            sender_node_id=self.node_id,
            timestamp=ts,
            hop_count=0,
            max_hops=max_hops,
            payload_type=payload_type,
            payload_data=data,
            signature_hmac=signature,
            is_verified=True
        )
        self.seen_packet_ids.add(pid)
        return packet

    def verify_and_ingest_packet(self, packet: MeshPacket) -> Tuple[bool, str]:
        """
        Validates packet authenticity, prevents replay attacks, checks hop limit,
        and verifies HMAC signature against tampering.
        """
        # Check duplicate
        if packet.packet_id in self.seen_packet_ids:
            return False, "DUPLICATE_PACKET_IGNORED"

        # Check hop limit
        if packet.hop_count >= packet.max_hops:
            return False, "MAX_HOPS_EXCEEDED"

        # Compute expected HMAC
        canonical_str = f"{packet.packet_id}:{packet.sender_node_id}:{packet.timestamp}:{packet.payload_type}:{json.dumps(packet.payload_data, sort_keys=True)}"
        expected_sig = hmac.new(self.secret_key, canonical_str.encode('utf-8'), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, packet.signature_hmac):
            return False, "INVALID_SIGNATURE_TAMPER_DETECTED"

        self.seen_packet_ids.add(packet.packet_id)
        packet.is_verified = True
        return True, "PACKET_VERIFIED_AND_ACCEPTED"

    def forward_packet(self, packet: MeshPacket) -> Optional[MeshPacket]:
        """Increments hop count for peer mesh relay."""
        if packet.hop_count >= packet.max_hops:
            return None

        relayed_pkt = packet.model_copy(deep=True)
        relayed_pkt.hop_count += 1
        return relayed_pkt


class DisasterAuditLedger:
    """
    Immutable, tamper-evident cryptographic log of all crisis requests,
    resource allocations, and humanitarian deliveries.
    Ensures 100% NGO/Donor accountability and eliminates disaster aid black-market leakage.
    """

    GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, node_id: str = "NODE-HUB-01"):
        self.node_id = node_id
        self.chain: List[LedgerBlock] = []
        self._init_genesis_block()

    def _init_genesis_block(self):
        """Initializes the genesis block."""
        genesis_data = {"message": "ResilioNet Humanitarian Genesis Block - HackSocial 2026"}
        genesis_hash = self._compute_block_hash(0, 0.0, self.GENESIS_PREV_HASH, "GENESIS", genesis_data)
        genesis_block = LedgerBlock(
            block_index=0,
            timestamp=0.0,
            previous_hash=self.GENESIS_PREV_HASH,
            event_type="GENESIS",
            event_payload=genesis_data,
            block_hash=genesis_hash,
            signer_node_id=self.node_id
        )
        self.chain.append(genesis_block)

    @staticmethod
    def _compute_block_hash(idx: int, ts: float, prev_hash: str, event_type: str, payload: Dict[str, Any]) -> str:
        payload_str = json.dumps(payload, sort_keys=True)
        header = f"{idx}:{ts}:{prev_hash}:{event_type}:{payload_str}"
        return hashlib.sha256(header.encode('utf-8')).hexdigest()

    def append_event(self, event_type: str, payload: Dict[str, Any]) -> LedgerBlock:
        """Appends a new verified event to the tamper-evident chain."""
        last_block = self.chain[-1]
        idx = len(self.chain)
        ts = time.time()
        block_hash = self._compute_block_hash(idx, ts, last_block.block_hash, event_type, payload)

        new_block = LedgerBlock(
            block_index=idx,
            timestamp=ts,
            previous_hash=last_block.block_hash,
            event_type=event_type,
            event_payload=payload,
            block_hash=block_hash,
            signer_node_id=self.node_id
        )
        self.chain.append(new_block)
        return new_block

    def verify_chain_integrity(self) -> Tuple[bool, Optional[str]]:
        """Validates all cryptographic hashes and linkage across the entire ledger."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            # Check previous hash link
            if curr.previous_hash != prev.block_hash:
                return False, f"Broken link at block index {curr.block_index}: previous_hash mismatch"

            # Check block hash computation
            expected_hash = self._compute_block_hash(
                curr.block_index, curr.timestamp, curr.previous_hash, curr.event_type, curr.event_payload
            )
            if curr.block_hash != expected_hash:
                return False, f"Tampered block detected at index {curr.block_index}: hash mismatch"

        return True, "LEDGER_INTEGRITY_VERIFIED"
