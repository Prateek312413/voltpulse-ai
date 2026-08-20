# ProcurePulse AI — 3-Minute Demo Video Script

**Target Duration**: 2 minutes 50 seconds  
**Voiceover Tone**: Professional, energetic, confident, authoritative.

---

### [0:00 - 0:30] Scene 1: The Problem (Hook & Context)
- **Visual**: Show a factory production floor or procurement spreadsheet with missing parts.
- **Narrator**: 
  > "Over 85% of industrial hardware distributors and parts suppliers do not have APIs. When an assembly line breaks or a project needs 250 high-pressure stainless steel ball valves, procurement teams spend hours stuck on phone calls asking for inventory stock, bargaining for volume discounts, and typing quotes into spreadsheets.
  > 
  > Today, we're introducing **ProcurePulse AI** — an autonomous supplier RFQ, price negotiation, and purchase order engine built on **CALL-E**."

---

### [0:30 - 1:15] Scene 2: Launching an RFQ Campaign & Live Call Wave
- **Visual**: Screen recording of ProcurePulse Workbench (`http://localhost:8000`). Show selecting an RFQ campaign (Part `SS-400-1-4`, target qty 250, target budget $45.00) and selecting 4 suppliers (Apex, Midwest, Titan, Precision).
- **Action**: Click the golden **"Launch CALL-E Negotiation Wave"** button.
- **Narrator**: 
  > "From our Procurement Workbench, we select our RFQ and choose four regional suppliers. With one click, ProcurePulse synthesizes tailored negotiation goals and dispatches parallel outbound phone calls via CALL-E.
  >
  > Notice the live console: as CALL-E connects to the supplier's sales desk, we see real-time audio waveforms and turn-by-turn dialogue streaming over WebSockets."

---

### [1:15 - 2:00] Scene 3: Intelligent Negotiation & Substitute Detection
- **Visual**: Zoom in on the transcript stream. Show the agent politely disclosing its identity, asking about stock, probing volume discount tiers ($42.50 at 250, $38.00 at 500), and asking about freight terms. Show Precision Metals offering a drop-in certified equivalent SKU `SS-400-1-4-EQUIV` at $39.50.
- **Narrator**: 
  > "Watch how CALL-E handles real-world business dynamics: it doesn't just ask for a price; it probes for tiered discounts, discovering that bumping our order to 500 units saves us 15%. 
  > 
  > When Precision Metals notes the OEM SKU is backordered, our agent asks for a certified form-fit-function replacement, capturing a $39.50 substitute that ships today."

---

### [2:00 - 2:35] Scene 4: Grounded Citations, MCDA Ranking & 1-Click PO
- **Visual**: Show the Multi-Supplier Bid Comparison Matrix populating. Show the MCDA score ranking suppliers. Click **"Evidence"** button to reveal the timestamped verbatim citation modal. Click **"Issue PO"** to open the approval modal.
- **Narrator**: 
  > "When the calls conclude, our extraction engine parses the conversation into structured data. Every single price, lead time, and freight term is backed by a verbatim timestamped citation from the audio transcript—eliminating hallucinations.
  > 
  > Our Multi-Criteria Decision Engine scores the bids across cost, delivery speed, and reliability rating, highlighting the best value bid and revealing over $3,800 in total savings.
  > 
  > Finally, our human purchasing manager reviews the evidence, clicks 'Confirm & Sync to ERP', and the formal Purchase Order is issued to SAP and Oracle NetSuite."

---

### [2:35 - 3:00] Scene 5: Architecture & Closing
- **Visual**: Show the architecture diagram, PR structure with `skills/`, `apps/`, `plugins/`, and test suite passing (`12 passed`).
- **Narrator**: 
  > "ProcurePulse is fully packaged with reusable Agent Skills, FastAPI backend, an n8n workflow plugin, and a comprehensive test suite.
  > 
  > With CALL-E, code isn't just generating text — it's picking up the phone and driving real-world industrial commerce. Thank you!"
