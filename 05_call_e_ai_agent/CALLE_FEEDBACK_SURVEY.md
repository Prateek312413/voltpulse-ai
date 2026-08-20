# CALL-E Platform Feedback & Technical Survey

**Participant Team**: ProcurePulse AI  
**Contribution Area**: Skills, Applications, Workflow Plugins  
**Platform Evaluated**: CALL-E CLI, Streamable HTTP MCP, Agent Skill Integration, Python SDK  

---

## 1. Executive Summary & Highlights
CALL-E provides a breakthrough abstraction for conversational AI agents. Moving beyond text generation to actual goal-driven telephony unlocks enormous enterprise value. 

During our development and stress-testing of **ProcurePulse AI**, we thoroughly exercised:
- The `calle` CLI (`auth status`, `call plan`, `call start`, `call run`, `call status`, `call recover`)
- The Streamable HTTP MCP endpoint (`plan_call`, `run_call`, `get_call_run`)
- Multi-party parallel dispatch and structured extraction workflows

Below is our structured technical feedback and concrete roadmap recommendations to help make CALL-E even more powerful for developers and enterprise builders.

---

## 2. Technical Strengths & What Worked Exceptionally Well

1. **Goal-Driven Reasoning vs. Script Trees**:
   - The standout feature of CALL-E is its ability to handle organic conversational deviations (e.g. sales rep offering a discount tier at 500 units or suggesting an alternative part number). It naturally stays on mission without getting tripped up by pleasantries, hold pauses, or clarification questions.
2. **Two-Stage Confirmation Token Model (`plan_call` -> `run_call`)**:
   - The requirement for an explicit `confirm_token` returned by `plan_call` before executing `run_call` is an outstanding safety architecture. It prevents accidental phone dials during dry-runs or agent planning loops.
3. **Idempotent Recovery Mechanism (`call recover`)**:
   - The CLI's private 0600 recovery cache for in-flight calls where the network dropped before receiving `run_id` provides enterprise reliability.

---

## 3. High-Value Opportunities for Improvement & Feature Requests

### A. Real-Time Streaming Webhooks & Audio WebSocket Feed
- **Current Behavior**: Clients must poll `get_call_run(run_id)` every 5–10 seconds after an initial delay to receive status and transcript updates.
- **Recommendation**: Introduce an optional server-side Webhook or Server-Sent Events (SSE) / WebSocket endpoint that pushes:
  1. `call.connected`
  2. `call.turn` (streaming partial transcript as words are spoken)
  3. `call.completed` (with final transcript and extracted summary)
- **Impact**: Enables real-time UI dashboards (like live audio waveforms and streaming transcript monitors) without aggressive polling overhead.

### B. Structured Output Schema Injection in `plan_call`
- **Current Behavior**: The agent returns free-form text transcripts and summaries that downstream applications must parse using secondary LLMs or regexes.
- **Recommendation**: Allow developers to pass an optional `output_schema` (JSON Schema / Pydantic definition) into `plan_call`. The CALL-E agent backend can then validate and return strict JSON in `call_run.structured_output`.
- **Impact**: Reduces latency and token costs by 40% for downstream business applications.

### C. First-Party Native Python SDK
- **Current Behavior**: Primary first-party SDK is TypeScript (`@call-e/calle`). Python developers currently interface via CLI subprocesses or FastMCP wrappers.
- **Recommendation**: Release an official `pip install call-e` package with native `asyncio` support, Pydantic types, and built-in exponential backoff polling.

### D. Multi-Number Wave Concurrency & Batch Throttling
- **Current Behavior**: Batch runners must manually manage concurrency limits and rate-limiting when placing 10+ calls simultaneously.
- **Recommendation**: Add a `batch_call` endpoint or CLI command (`calle call batch --file leads.jsonl --concurrency 3`) with built-in pacing and carrier rate-limit handling.

### E. Disclosed Transfer to Live Human Agent (`human_handoff`)
- **Current Behavior**: If an inquiry requires complex engineering sign-off, the call simply ends with a note.
- **Recommendation**: Provide a tool primitive where CALL-E can execute a SIP / PSTN warm transfer (e.g. transfer call to a human supervisor's desk line) when specific intent triggers are met.

---

## 4. Minor Developer Experience (DX) Friction Points & Fixes

1. **Metadata Parameter Passing in MCP**:
   - Passing custom customer metadata at the top level of MCP arguments causes `Unexpected keyword argument: metadata`. Documenting the `{"call-e/customerMetadata": ...}` format in the root README resolved this, but a dedicated `custom_metadata` argument in `plan_call` would be cleaner.
2. **CLI JSON Flag Consistency**:
   - `calle auth status --json` output format varies slightly across operating systems. Standardizing all non-help CLI stdout to guaranteed strict JSON simplifies subprocess parsing on Windows and Linux.

---

## 5. Conclusion
CALL-E is one of the most exciting developer platforms in the AI agent ecosystem today. We hope this feedback helps shape the future roadmap and telemetry features as CALL-E expands to millions of calls worldwide!
