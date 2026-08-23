# AegisMed: Resilient Clinical Agentic Memory Engine
### CockroachDB × AWS Hackathon — Official Submission

[![Tests](https://img.shields.io/badge/pytest-18%20passed%20(100%25)-success?style=for-the-badge)](tests/)
[![CockroachDB](https://img.shields.io/badge/CockroachDB-Distributed%20SQL%20%2B%20pgvector-blue?style=for-the-badge&logo=cockroachlabs)](https://www.cockroachlabs.com/)

[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude%203.5%20%26%20Titan-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)


---

## 1. Executive Summary

In high-stakes domains like healthcare, AI agents cannot afford **"context amnesia"**, lost historical allergies, or corrupt memory states when asynchronous telemetry arrives out of order.

**AegisMed** is an enterprise-grade **Clinical Multi-Agent Intelligence System** engineered around a **Hierarchical 4-Tier Agentic Memory Architecture with Bayesian Uncertainty Quantification and Late-Telemetry Reconciliation**, powered by **CockroachDB Serverless / Distributed SQL + pgvector** and **AWS (Bedrock Claude 3.5 Sonnet, Titan Text Embeddings, S3 & Lambda)**.

```
+-----------------------------------------------------------------------------------------+
|                                    AEGISMED ARCHITECTURE                                |
|                                                                                         |
|  [Clinician Console UI] <---> [FastAPI REST / WebSocket Gateway]                        |
|                                         |                                               |
|                    +--------------------+---------------------+                         |
|                    |     Multi-Agent Clinical Swarm           |                         |
|                    |  • Triage Agent (Acuity Stratification)  |                         |
|                    |  • Diagnostic Agent (Hypotheses)         |                         |
|                    |  • Pharmacovigilance (Safety & Allergies)|                         |
|                    |  • Reflection Agent (Longitudinal Drift) |                         |
|                    |  • Uncertainty & Late-Telemetry Reconciler|                        |
|                    +--------------------+---------------------+                         |
|                                         |                                               |
|  +--------------------------------------+--------------------------------------------+  |
|  |                 COCKROACHDB DISTRIBUTED AGENTIC MEMORY ENGINE                     |  |
|  |                                                                                   |  |
|  |   [Tier 1: Working Memory]     [Tier 2: Episodic Memory]                          |  |
|  |   • ACID Transactional Locks   • Longitudinal Encounters                          |  |
|  |   • Optimistic Concurrency     • High-Dim Vector Search (pgvector)                |  |
|  |                                                                                   |  |
|  |   [Tier 3: Semantic Memory]    [Tier 4: Reflective Memory]                        |  |
|  |   • Clinical Guidelines        • Autonomous Meta-Insights                         |  |
|  |   • Drug Contraindication DB   • Out-of-Order Telemetry Reconciler                |  |
|  +--------------------------------------+--------------------------------------------+  |
|                                         |                                               |
|        [AWS Bedrock: Claude 3.5 & Titan] <---> [AWS S3 Reports & AWS Lambda]            |
+-----------------------------------------------------------------------------------------+
```

---

## 2. The 4-Tier Memory Hierarchy

| Tier | Memory Type | CockroachDB Storage Mechanism | Clinical Function |
|---|---|---|---|
| **Tier 1** | **Working Memory** | Relational tables with `SERIALIZABLE` isolation & distributed row locks | Maintains transient session state, vital signs streams, active hypotheses, and prevents multi-agent write collisions. |
| **Tier 2** | **Episodic Memory** | Hybrid SQL + High-Dimensional Vector Embeddings (pgvector compatibility) | Indexes longitudinal patient encounters, doctor notes, and past allergic reactions with cosine similarity distance search. |
| **Tier 3** | **Semantic Memory** | Rule ontologies + Vectorized medical guidelines | Clinical practice rules, drug-drug interaction matrices, and contraindications. |
| **Tier 4** | **Reflective Meta-Memory** | Async meta-cognition tables with causal edge links | Synthesizes multi-visit trajectories, reconciles late telemetry, and flags progressive organ deterioration with Bayesian GPR ($\pm 1.96\sigma$). |

---

## 3. Quick Start & One-Click Launch

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/Prateek312413/battery-health-forecast-engine.git aegismed
cd aegismed

# 2. Install dependencies
pip install -r requirements.txt
```

### Launch Clinician Console
```bash
python run_aegismed.py
```
> *Your browser will automatically open to `http://localhost:8000` with the interactive Clinician Console.*

### Run Automated Test Suite (18/18 Tests Passing)
```bash
pytest tests/ -v
```

---

## 4. Benchmark Clinical Scenarios

* **Scenario 1: Marcus Vance (P-1001) — Allergy Safety Shield:** Diagnostic Agent proposes Amoxicillin $\rightarrow$ Pharmacovigilance Agent queries CockroachDB vector memory, retrieves 14-month-old severe anaphylactic reaction, triggers `CRITICAL_ALERT`, blocks Amoxicillin, and approves safe Azithromycin.
* **Scenario 2: Elena Rostova (P-1002) — Renal Trajectory & Late Telemetry:** Reflection Agent detects progressive Stage 3 CKD decline, fits a Gaussian Process Bayesian trajectory curve with 95% confidence bounds, and deterministically reconciles out-of-order lab telemetry in CockroachDB.
* **Scenario 3: David Chen (P-1003) — Cardiovascular Emergency:** Immediate `CRITICAL` acuity lock in Tier-1 Working Memory, emergency protocol activation, and instant acute coronary syndrome differential.

---

## 📁 Repository Directory Structure & Hackathon Hub

```
├── 01_cockroachdb_aws_hackathon/   <-- AegisMed: Standalone Packaging & Assets
├── 02_retrieve_reverie_hacks/      <-- SynapseFlow: Reverie Hacks 2026 Submission
├── 04_volthacks_2026/              <-- VoltPulse AI: VoltHacks 2026 1st Place Submission
├── 07_neuralsprint_2026/           <-- NeuroAccess AI: NeuralSprint Submission
├── 08_hacksocial_2026/             <-- ResilioNet AI: HackSocial Submission
├── 11_proof_of_possible_2026/      <-- EvidenceMesh: Proof of Possible 2026 Submission
├── 12_midnight_bioveil_zk/         <-- BioVeil: Midnight ZK Privacy Submission
├── 13_catalyst_2026/               <-- ObsidioCore: CISSA Catalyst 2026 Flagship Submission
├── 14_gatewaygs_2026/              <-- TerraPulse AI: GatewayGS AI 4 Earth Submission
├── 15_prompt_wars_2026/            <-- PromptShield AI: Prompt Wars 2026 Flagship Submission
├── 16_impact_forge_2026/            <-- Impact Forge 2026 Submission
├── 17_brainwave_2026/               <-- AegisCredit ZK: Brainwave 2026 Midnight Track Submission
├── 18_prometheus_august_ai_challenge/ <-- Promethea AI: Prometheus August AI Challenge Grand Prize Submission
├── aegismed/                       <-- Core AegisMed Application Package
│   ├── agents/                     <-- Triage, Diagnostic, Pharma, Reflection, Swarm Orchestrator
│   ├── database/                   <-- CockroachDB Models, Migrations, Connection Pool
│   ├── mcp/                        <-- Model Context Protocol (MCP) Server
│   ├── memory/                     <-- 4-Tier Memory Engine (Working, Episodic, Semantic, Reflective)
│   ├── ml/                         <-- Gaussian Process Bayesian Uncertainty Engine
│   └── static/                     <-- Interactive Clinician Console (Dark Mode Dashboard)
├── tests/                          <-- 18 Comprehensive Pytest Unit & Integration Tests
├── run_aegismed.py                 <-- One-Click Zero-Config Auto-Browser Launcher
└── LICENSE                         <-- Open Source MIT License
```
