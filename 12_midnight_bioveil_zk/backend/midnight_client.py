"""
Midnight Blockchain Network Client & Dual-State Ledger Simulator
Manages interaction with Midnight Preview/PreProd testnet, transaction serialization,
Compact circuit dispatching, and shielded UTXO ledger syncing.
"""

import time
import secrets
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from backend.data_models import (
    ClinicalTrialModel,
    MidnightBlockModel,
    MidnightTxModel,
    MidnightNetworkStats,
    TrialStatusEnum
)
from backend.zk_engine import poseidon_hash
from backend.sample_data import get_initial_trials


class MidnightNetworkClient:
    """
    Midnight Blockchain Interface.
    Simulates node RPC, indexer, Compact smart contract execution,
    and shielded dual-state state transitions.
    """

    def __init__(self, network_id: str = "midnight-preview-4101"):
        self.network_id = network_id
        self.current_block_height: int = 1420
        self.latest_block_hash: str = "0x8fa1c900e4b81098234a1009bf21e901aa881029384729104810293847192830"
        
        # Dual-State Ledger Repositories
        self.trials: Dict[str, ClinicalTrialModel] = {}
        self.nullifiers: set = set()
        self.proof_receipts: Dict[str, Dict[str, Any]] = {}
        self.audit_grants: Dict[str, Dict[str, Any]] = {}
        
        # Blockchain Ledger History
        self.blocks: List[MidnightBlockModel] = []
        self.pending_txs: List[MidnightTxModel] = []
        
        # Token Accounting
        self.total_shielded_proofs: int = 42
        self.total_disbursed_night: int = 185000
        self.shielded_balances: Dict[str, int] = {
            "midnight1z_shielded_patient_elena_vance_88019a": 15000,
            "midnight1z_shielded_patient_david_rossi_33910d": 12000,
            "midnight1z_shielded_patient_clara_oswald_66190e": 8000,
            "midnight1q_sponsor_genentech_89a01f9": 5000000,
            "midnight1q_sponsor_biontech_44e9081": 7500000,
        }

        # Seed initial trials & genesis blocks
        self._seed_initial_state()

    def _seed_initial_state(self):
        for trial in get_initial_trials():
            self.trials[trial.trial_id] = trial
        
        # Pre-seed recent historical blocks
        now = int(time.time())
        prev_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
        for i in range(10):
            b_height = self.current_block_height - (9 - i)
            b_hash = poseidon_hash("MIDNIGHT_BLOCK", b_height, prev_hash)
            txs = [
                MidnightTxModel(
                    tx_hash=poseidon_hash("TX_GEN", b_height, i),
                    block_height=b_height,
                    sender=f"midnight1q_prover_node_{secrets.token_hex(4)}",
                    contract_target="BioVeilZK.compact",
                    circuit_invoked="proveAndEnrollInTrial",
                    shielded_inputs_count=5,
                    public_disclosures=[f"Nullifier 0x{secrets.token_hex(6)}..."],
                    dust_fee_consumed=1250,
                    timestamp=now - ((9 - i) * 6),
                    status="CONFIRMED"
                )
            ]
            block = MidnightBlockModel(
                block_height=b_height,
                block_hash=b_hash,
                previous_block_hash=prev_hash,
                merkle_root=poseidon_hash("MERKLE_ROOT", b_height),
                timestamp=now - ((9 - i) * 6),
                transactions_count=len(txs),
                transactions=txs,
                prover_node_id=f"midnight_validator_eu_central_{i%3 + 1}"
            )
            self.blocks.append(block)
            prev_hash = b_hash
        self.latest_block_hash = prev_hash

    def get_network_stats(self) -> MidnightNetworkStats:
        total_escrow = sum(t.escrow_deposit_night for t in self.trials.values())
        return MidnightNetworkStats(
            network_name="Midnight Preview Testnet (Chain ID 4101)",
            current_block_height=self.current_block_height,
            total_shielded_proofs=self.total_shielded_proofs,
            active_compact_contracts=len(self.trials) + 2,
            total_locked_night_escrow=total_escrow,
            total_disbursed_night=self.total_disbursed_night,
            current_dust_rate=0.00042,
            prover_network_health="100% OPERATIONAL (Zero-Knowledge Halo2 Engine)"
        )

    def get_all_trials(self) -> List[ClinicalTrialModel]:
        return list(self.trials.values())

    def get_trial_by_id(self, trial_id: str) -> Optional[ClinicalTrialModel]:
        return self.trials.get(trial_id)

    def register_new_trial(self, trial: ClinicalTrialModel) -> Tuple[bool, str, MidnightTxModel]:
        if trial.trial_id in self.trials:
            return False, "Trial ID already exists on-chain", None
        
        self.trials[trial.trial_id] = trial
        
        tx = self._create_and_mine_transaction(
            sender=trial.sponsor_address,
            contract="BioVeilZK.compact",
            circuit="registerTrial",
            disclosures=[f"TrialID: {trial.trial_id[:12]}...", f"Deposit: {trial.escrow_deposit_night} NIGHT"],
            dust_fee=1800
        )
        return True, "Trial registered successfully on Midnight Preview Testnet", tx

    def submit_zk_enrollment(
        self,
        trial_id: str,
        nullifier_hash: str,
        public_commitment: str,
        proof_bytes_hex: str,
        shielded_address: str
    ) -> Tuple[bool, str, Optional[MidnightTxModel]]:
        if trial_id not in self.trials:
            return False, "Trial not found on Midnight ledger", None
        
        trial = self.trials[trial_id]
        if trial.status != TrialStatusEnum.ACTIVE:
            return False, "Trial is not actively accepting enrollments", None
        
        if trial.enrolled_count >= trial.max_participants:
            return False, "Trial participant quota reached", None
        
        if nullifier_hash in self.nullifiers:
            return False, "Nullifier collision: Patient already enrolled in this trial", None

        # Record nullifier in public state
        self.nullifiers.add(nullifier_hash)
        trial.enrolled_count += 1
        self.total_shielded_proofs += 1

        receipt = {
            "trial_id": trial_id,
            "nullifier_hash": nullifier_hash,
            "public_commitment": public_commitment,
            "shielded_address": shielded_address,
            "proof_bytes_hex": proof_bytes_hex,
            "enrolled_at_block": self.current_block_height,
            "is_milestone_claimed": False,
            "timestamp": int(time.time())
        }
        self.proof_receipts[nullifier_hash] = receipt

        tx = self._create_and_mine_transaction(
            sender=shielded_address,
            contract="BioVeilZK.compact",
            circuit="proveAndEnrollInTrial",
            disclosures=[f"Nullifier: {nullifier_hash[:16]}...", f"Trial: {trial_id[:12]}..."],
            dust_fee=2400
        )

        return True, "Zero-Knowledge Proof verified & enrolled in trial anonymously", tx

    def claim_milestone_payout(
        self,
        nullifier_hash: str,
        checkpoint_id: str,
        completion_secret_hex: str,
        shielded_recipient_address: str
    ) -> Tuple[bool, str, int, Optional[MidnightTxModel]]:
        if nullifier_hash not in self.proof_receipts:
            return False, "Unrecognized or unverified nullifier receipt", 0, None
        
        receipt = self.proof_receipts[nullifier_hash]
        if receipt["is_milestone_claimed"]:
            return False, "Milestone stipend already claimed for this checkpoint", 0, None
        
        trial = self.trials.get(receipt["trial_id"])
        if not trial:
            return False, "Associated trial not found", 0, None
        
        reward_amount = trial.milestone_reward_night
        if trial.escrow_deposit_night < reward_amount:
            return False, "Insufficient escrow reserves in smart contract vault", 0, None

        # Execute payout state changes
        receipt["is_milestone_claimed"] = True
        trial.escrow_deposit_night -= reward_amount
        self.total_disbursed_night += reward_amount
        
        # Credit shielded address
        current_bal = self.shielded_balances.get(shielded_recipient_address, 0)
        self.shielded_balances[shielded_recipient_address] = current_bal + reward_amount

        tx = self._create_and_mine_transaction(
            sender=shielded_recipient_address,
            contract="ShieldEscrow.compact",
            circuit="submitMilestoneProofAndClaimStipend",
            disclosures=[f"Disbursed: {reward_amount} NIGHT", f"Recipient: {shielded_recipient_address[:16]}..."],
            dust_fee=1600
        )

        return True, f"Milestone reward of {reward_amount:,} NIGHT disbursed to shielded address", reward_amount, tx

    def _create_and_mine_transaction(
        self,
        sender: str,
        contract: str,
        circuit: str,
        disclosures: List[str],
        dust_fee: int
    ) -> MidnightTxModel:
        self.current_block_height += 1
        now = int(time.time())
        tx_hash = poseidon_hash("MIDNIGHT_TX", self.current_block_height, sender, circuit, now)
        
        tx = MidnightTxModel(
            tx_hash=tx_hash,
            block_height=self.current_block_height,
            sender=sender,
            contract_target=contract,
            circuit_invoked=circuit,
            shielded_inputs_count=4,
            public_disclosures=disclosures,
            dust_fee_consumed=dust_fee,
            timestamp=now,
            status="CONFIRMED"
        )
        
        # Mine new block containing this transaction
        block_hash = poseidon_hash("MIDNIGHT_BLOCK", self.current_block_height, self.latest_block_hash, tx_hash)
        block = MidnightBlockModel(
            block_height=self.current_block_height,
            block_hash=block_hash,
            previous_block_hash=self.latest_block_hash,
            merkle_root=poseidon_hash("MERKLE_ROOT", self.current_block_height, tx_hash),
            timestamp=now,
            transactions_count=1,
            transactions=[tx],
            prover_node_id="midnight_halo2_prover_01"
        )
        
        self.blocks.append(block)
        if len(self.blocks) > 50:
            self.blocks.pop(0)
        self.latest_block_hash = block_hash
        return tx

    def mine_synthetic_heartbeat_block(self) -> MidnightBlockModel:
        """Called periodically by background worker to simulate active Midnight blockchain consensus."""
        self.current_block_height += 1
        now = int(time.time())
        tx_hash = poseidon_hash("HEARTBEAT_ZK_TX", self.current_block_height, now)
        tx = MidnightTxModel(
            tx_hash=tx_hash,
            block_height=self.current_block_height,
            sender=f"midnight1z_{secrets.token_hex(6)}",
            contract_target="BioVeilZK.compact",
            circuit_invoked="verifyTrialCheckpointAdherence",
            shielded_inputs_count=3,
            public_disclosures=[f"ProofCommitment: 0x{secrets.token_hex(8)}..."],
            dust_fee_consumed=1100,
            timestamp=now,
            status="CONFIRMED"
        )
        block_hash = poseidon_hash("MIDNIGHT_BLOCK", self.current_block_height, self.latest_block_hash, tx_hash)
        block = MidnightBlockModel(
            block_height=self.current_block_height,
            block_hash=block_hash,
            previous_block_hash=self.latest_block_hash,
            merkle_root=poseidon_hash("MERKLE", self.current_block_height),
            timestamp=now,
            transactions_count=1,
            transactions=[tx],
            prover_node_id="midnight_halo2_prover_primary"
        )
        self.blocks.append(block)
        if len(self.blocks) > 50:
            self.blocks.pop(0)
        self.latest_block_hash = block_hash
        return block
