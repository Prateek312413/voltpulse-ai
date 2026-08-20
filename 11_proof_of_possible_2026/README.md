# EvidenceMesh: Autonomous Causal Verification & Cryptographic Proof Engine
### Proof of Possible 2026 Devpost Hackathon — Official Submission

[![Tests](https://img.shields.io/badge/pytest-16%20passed%20(100%25)-success?style=for-the-badge)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=for-the-badge&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> *"Don’t pitch the future. Build evidence."*

---

## 1. Executive Summary

Generative AI models make impressive, articulate assertions, but in safety-critical domains (medicine, clean energy engineering, autonomous cyber defense, regulatory compliance), unverified claims and hallucinations lead to catastrophic failure modes.

**EvidenceMesh** is an enterprise-grade **Autonomous Causal Verification & Cryptographic Proof Engine**. Instead of treating AI as an opaque text generator, EvidenceMesh decomposes complex propositions into discrete atomic assertions, constructs a causal dependency Directed Acyclic Graph (DAG), executes multi-agent adversarial cross-examination (red-teaming), computes calibrated Bayesian uncertainty intervals ($\pm 1.96\sigma$, ECE, Brier score), and issues tamper-evident SHA-256 Merkle Proof Certificates.

```
+---------------------------------------------------------------------------------------------------+
|                                      EVIDENCEMESH ARCHITECTURE                                    |
|                                                                                                   |
|  [Interactive Glassbox Console] <== WebSockets / REST ==> [FastAPI Verification Gateway]          |
|                                                                     |                             |
|              +------------------------------------------------------+---------------------+       |
|              |                  Multi-Agent Adversarial Audit Swarm                        |       |
|              |  • Claim Decomposition Agent (Atomic Fact Extraction)                      |       |
|              |  • Multimodal Retrieval & Citation Agent (Ground-Truth Ingestion)           |       |
|              |  • Adversarial Cross-Examiner (Red-Teaming & Fallacy Detection)             |       |
|              |  • Causal DAG Synthesizer (Dependency Resolution & Cycle Detection)         |       |
|              |  • Bayesian Uncertainty & Calibration Calibrator (ECE, Brier, ±1.96σ)       |       |
|              +------------------------------------------------------+---------------------+       |
|                                                                     |                             |
|  +------------------------------------------------------------------+--------------------------+  |
|  |                           CORE VERIFICATION & CRYPTOGRAPHIC ENGINE                           |  |
|  |                                                                                             |  |
|  |   [Atomic Claim DAG]                 [Bayesian Epistemic Engine]                            |  |
|  |   • Directed Acyclic Graph           • Epistemic vs Aleatoric Uncertainty                   |  |
|  |   • Causal Inference & Entailment    • Beta-Binomial / GPR Calibration                      |  |
|  |                                                                                             |  |
|  |   [Cryptographic Proof Ledger]       [Tamper-Proof Export & Audit]                          |  |
|  |   • SHA-256 Merkle Evidence Root     • Verifiable JSON-LD Proof Certificates                |  |
|  |   • Immutable Audit Lineage          • One-Click PDF/JSON Report Generation                 |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Mathematical Rigor & Uncertainty Formulation

### A. Bayesian Beta-Binomial Belief Updating
Given prior skepticism parameters $\alpha_0, \beta_0$, observed positive evidence weights $w_i \cdot c_i$, and refuting evidence weights $w_j \cdot (1 - c_j)$, the posterior belief distribution follows:
$$\alpha_{\text{post}} = \alpha_0 + \sum_{i=1}^{N_{\text{pos}}} w_i \cdot c_i, \quad \beta_{\text{post}} = \beta_0 + \sum_{j=1}^{N_{\text{neg}}} w_j \cdot (1 - c_j + 0.5)$$

$$\mathbb{E}[\theta] = \frac{\alpha_{\text{post}}}{\alpha_{\text{post}} + \beta_{\text{post}}}$$

$$\text{Var}(\theta) = \frac{\alpha_{\text{post}} \cdot \beta_{\text{post}}}{(\alpha_{\text{post}} + \beta_{\text{post}})^2 (\alpha_{\text{post}} + \beta_{\text{post}} + 1)}$$

$$95\% \text{ Credible Interval} = \left[ \mathbb{E}[\theta] - 1.96 \sqrt{\text{Var}(\theta)}, \; \mathbb{E}[\theta] + 1.96 \sqrt{\text{Var}(\theta)} \right]$$

### B. Expected Calibration Error (ECE) & Reliability Scoring
To prevent overconfident hallucinations, claims are grouped into $M$ confidence bins $B_m$:
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

### C. Cryptographic Merkle Evidence Tree
Every atomic claim is hashed into an immutable leaf node with its semantic citations and confidence level:
$$h_i = \text{SHA256}(\text{Domain} \,||\, \text{ClaimID} \,||\, \text{Status} \,||\, \text{Confidence} \,||\, \text{Citations})$$
$$h_{\text{root}} = \text{MerkleTree}(\{h_1, h_2, \dots, h_k\})$$

---

## 3. Quick Start & Launcher

### Installation
```bash
# Clone the repository
git clone https://github.com/Prateek312413/BrainWave.git
cd BrainWave

# Install lightweight dependencies
pip install -r requirements.txt
```

### Launch Interactive Web Console
```bash
python run.py
```
> *Your browser will automatically open to `http://localhost:8000` with the dark-mode interactive console.*

### Run Full Test Suite (16/16 Tests Passing)
```bash
python run.py --test
# or
pytest tests/ -v
```

---

## 4. Empirical Benchmark Scenarios

1. **Clinical Trial Renal Protection & Allergy Shield**: Evaluates Empagliflozin SGLT2 eGFR 28% decline reduction against a severe IgE-mediated beta-lactam anaphylaxis contraindication, instantly blocking fatal cross-reactivity.
2. **Solid-State Battery 450 Wh/kg Energy Density & 4C Fast Charging**: Corroborates 450 Wh/kg energy density and 800-cycle life under 5 MPa pressure from *Nature Materials*, while refuting unmanaged 4C fast charging.
3. **Autonomous AI Code Synthesis Safety**: Audits 18.4% vulnerable package import rate and 92% multi-agent reduction from *arXiv:2501.08942*, while refuting "100% bug-free" claims.
4. **Corporate ESG Carbon Neutrality**: Validates Scope 3 ISO 14064 requirements while catching Scope 1 REC misattributions.

---

## 5. Repository Directory Layout

```
11_proof_of_possible_2026/
├── evidencemesh/
│   ├── core/
│   │   ├── claim_decomposer.py     <-- Atomic Predicate Extraction
│   │   ├── causal_graph.py         <-- DAG Dependency & Cycle Detection
│   │   ├── bayesian_calibrator.py  <-- Beta-Binomial, ECE, Brier Score
│   │   ├── merkle_ledger.py        <-- Cryptographic SHA-256 Merkle Proofs
│   │   └── verifier.py             <-- Multi-Tier Empirical Verifier
│   ├── agents/
│   │   ├── extractor.py            <-- Proposition Decomposer Agent
│   │   ├── cross_examiner.py       <-- Adversarial Red-Teamer Agent
│   │   ├── synthesizer.py          <-- Consensus Synthesizer Agent
│   │   └── swarm.py                <-- Multi-Agent Swarm Orchestrator
│   ├── knowledge/
│   │   ├── corpus.py               <-- Ground-Truth Empirical Corpus
│   │   └── benchmark_scenarios.py  <-- 4 Rich Pre-Configured Scenarios
│   ├── api/
│   │   ├── routes.py               <-- REST Endpoints
│   │   └── websocket.py            <-- Live Streaming Pipeline
│   ├── static/
│   │   └── index.html              <-- Glassmorphic Dark UI & DAG Canvas
│   ├── config.py                   <-- Project Configuration
│   ├── models.py                   <-- Pydantic V2 Domain Models
│   └── main.py                     <-- FastAPI App Entrypoint
├── tests/                          <-- 16 Comprehensive Pytest Unit Tests
├── run.py                          <-- One-Click Auto-Browser Launcher
├── requirements.txt                <-- Python Dependencies
├── DEVPOST_SUBMISSION.md           <-- Pre-Filled Devpost Submission Text
├── README.md                       <-- System Documentation
└── LICENSE                         <-- Open Source MIT License
```

---

## 6. License
MIT License. Open-source for researchers, engineers, and developers.
