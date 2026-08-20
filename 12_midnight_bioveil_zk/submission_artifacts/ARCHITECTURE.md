# BioVeil ZK — Technical Architecture & Compact Circuit Specification

## 1. Dual-State Architecture Overview

Midnight blockchain introduces a paradigm-shifting **dual-state execution environment**:
1. **Private State (Witness)**: Private patient attributes (raw EHR records, exact age, DOB, blood panel, genetic markers, encryption keys) that exist exclusively on the patient's local off-chain client.
2. **Public State (Ledger)**: Global immutable state published on Midnight blockchain (registered trial parameters, participant caps, blinded nullifiers, shielded milestone escrow balances, and auditor viewing registry).

```
 ┌────────────────────────────────────────────────────────┐
 │            OFF-CHAIN PATIENT CLIENT (WITNESS)          │
 │                                                        │
 │  EHR Records  -->  Witness Fetcher  -->  ZK Prover     │
 │  (Age, DNA)         (Private State)       (Poseidon)   │
 └───────────────────────────┬────────────────────────────┘
                             │
            ZK-SNARK Proof   │  Public Blinded Nullifier
            (384 bytes)      │  0x7f8812c...
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │           ON-CHAIN MIDNIGHT BLOCKCHAIN LEDGER          │
 │                                                        │
 │  BioVeilZK.compact  <--->  ShieldEscrow.compact        │
 │  (Circuit Asserts)         (NIGHT / DUST Escrow)       │
 │                                                        │
 │  Nullifier Set      <--->  AuditCompliance.compact     │
 │  (Double-claim guard)      (Viewing Keys)              │
 └────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical Circuit Constraints

### Circuit 1: `proveAndEnrollInTrial`
$$\text{Private Inputs (Witness): } \langle \text{Age}, \text{Biomarker}, \text{eGFR}, \text{BP}_{sys}, \text{CondMask}, \text{Secret} \rangle$$
$$\text{Public Inputs (Ledger): } \langle \text{TrialID}, \text{MinAge}, \text{MaxAge}, \text{TargetBioHash}, \text{MinEgfr}, \text{MaxBP}, \text{ExclMask} \rangle$$

**Constraints Enforced:**
1. **Age Range**:
   $$\text{Assert}(\text{Age} \ge \text{MinAge} \land \text{Age} \le \text{MaxAge})$$
2. **Biomarker Hash Match**:
   $$\text{Assert}(\text{Poseidon}(\text{"BIOMARKER\_LOCUS\_TAG"}, \text{Biomarker}) == \text{TargetBioHash})$$
3. **Renal Function Threshold**:
   $$\text{Assert}(\text{eGFR} \ge \text{MinEgfr})$$
4. **Cardiovascular Safety Bound**:
   $$\text{Assert}(\text{BP}_{sys} \le \text{MaxBP})$$
5. **Comorbidity Disjointness**:
   $$\text{Assert}((\text{CondMask} \ \& \ \text{ExclMask}) == 0)$$
6. **Blinded Nullifier Derivation**:
   $$\text{Nullifier} = \text{Poseidon}(\text{"MIDNIGHT\_NULLIFIER"}, \text{TrialID}, \text{Secret})$$
   $$\text{Assert}(\text{Nullifier} \notin \text{Ledger}.\text{enrolledNullifiers})$$

---

## 3. Cryptographic Primitives

| Primitive | Parameter | Implementation | Purpose |
| :--- | :--- | :--- | :--- |
| **Field Modulus** | $2^{254}$ prime | Pasta (Pallas / Vesta) | Midnight Compact native curve arithmetic |
| **Hash Function** | Poseidon Sponge | 32-byte digest | Fast ZK-friendly cryptographic hashing |
| **Proof System** | Halo2-IPA | 384-byte succinct proof | Zero-Knowledge proof of constraint satisfaction |
| **Nullifier** | PRF commitment | Keyed Poseidon hash | Double-enrollment prevention without identity leakage |
| **Viewing Key** | Diffie-Hellman / BLS | Asymmetric encryption | Selective disclosure to authorized FDA/IRB auditors |

---

## 4. Smart Contract Specifications

### `BioVeilZK.compact`
- `ledger trials: Map<Bytes<32>, TrialState>`: Stores registered trials.
- `ledger enrolledNullifiers: Set<Bytes<32>>`: Records unique nullifiers to prevent duplicate submissions.
- `ledger proofReceipts: Map<Bytes<32>, VerificationProofReceipt>`: Verifiable on-chain enrollment records.
- `circuit proveAndEnrollInTrial()`: Evaluates ZK constraints, asserts conditions, updates ledger state.

### `ShieldEscrow.compact`
- `ledger vaults: Map<Bytes<32>, EscrowVault>`: Manages locked NIGHT tokens.
- `circuit executeShieldedPayout()`: Unlocks stipend and transfers NIGHT directly to shielded address.

### `AuditCompliance.compact`
- `ledger authorizedAuditors: Map<Address, AuditorCredentials>`: Validates regulatory credentials.
- `circuit issueAuditGrant()`: Grants time-limited viewing keys to authorized inspectors.
- `circuit verifyAuditAccess()`: Validates auditor signatures.
