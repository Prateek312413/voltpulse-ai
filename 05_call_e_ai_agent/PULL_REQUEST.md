# Pull Request: Add ProcurePulse AI (Agent Skill, App & n8n Plugin)

**Target Repository**: `CALLE-AI/awesome-phone-call-agents`  
**Base Branch**: `main`  
**PR Title**: `feat: add ProcurePulse AI - autonomous industrial supplier RFQ & negotiation phone agent`

---

## 📌 Summary of Changes

This PR introduces **ProcurePulse AI** across all three contribution areas:

1. **`skills/procure-pulse-negotiator/` (Agent Skill)**:
   - Reusable CALL-E Agent Skill for industrial hardware, manufacturing components, and MRO procurement RFQ phone calls.
   - Probes tiered volume pricing (e.g., 250, 500, 1000 units), lead times, and FOB shipping terms.
   - Detects certified form-fit-function substitute SKUs when primary parts are backordered.
   - Strict safety boundaries: Discloses AI identity, never commits to purchases, and strictly enforces zero payment disclosure on call.

2. **`apps/procure-pulse-workbench/` (User-Facing Application)**:
   - Full-stack Python & FastAPI application with modern Tailwind CSS glassmorphic dashboard.
   - Real-time animated audio waveform visualizer and streaming transcript console over WebSockets.
   - High-fidelity realistic supplier call simulation sandbox for zero-credit test evaluation + Live CALL-E outbound dialing bridge.
   - Multi-Criteria Decision Analysis (MCDA) bid scoring matrix and verbatim timestamped citation inspector.
   - 1-click PO approval modal with printable ISO-compliant PO view and ERP webhook triggers.

3. **`plugins/procure-pulse-n8n/` (Workflow Plugin)**:
   - Ready-to-import n8n workflow JSON template automating RFQs from Airtable/ERP to ProcurePulse wave calls to Slack alerts.

---

## 🧪 Testing & Verification

- **Automated Tests**: Comprehensive Pytest suite covering schema validation, transcript extraction, MCDA ranking, and API endpoints (`pytest tests/ -v` -> `12/12 passed`).
- **Benchmark Suite**: Verified low latency in `benchmark.py` (0.005 ms prompt synthesis, 0.039 ms extraction).
- **Dry-Run Script**: Verified standalone execution in `skills/procure-pulse-negotiator/scripts/dry_run_test.py`.

---

## 📋 Checklist

- [x] Conforms to the `awesome-phone-call-agents` README template and contribution guidelines.
- [x] Includes explicit dry-run / sandbox preview mode without placing real calls.
- [x] Explicit identity disclosure and anti-commitment financial safety gates included in prompts.
- [x] Pydantic schemas and output structures validated with tests.
- [x] Reusable across any skills.sh or CALL-E compatible agent host.
