# ProcurePulse n8n Workflow Plugin

Automate industrial supply chain Request for Quote (RFQ) voice calls and PO generation using **ProcurePulse** and **CALL-E** directly from your ERP or spreadsheet.

## Architecture

```
[Airtable / Google Sheets / ERP] 
       │ (Trigger on new BOM / Part Request)
       ▼
[n8n Webhook Node]
       │
       ▼
[ProcurePulse Dispatcher (CALL-E Outbound)]
       │ (Parallel Voice RFQs to Suppliers)
       ▼
[ProcurePulse MCDA Evaluator]
       │ (Structured Quotes + Grounded Citations)
       ▼
[n8n Slack/Email Approval Gate]
       │ (Human Purchasing Manager 1-Click Approval)
       ▼
[ProcurePulse PO Generator] ──► [SAP / NetSuite / Airtable ERP Sync]
```

## Setup & Installation

1. Import `workflow.json` into your n8n workspace (`Workflows -> Import from File`).
2. Set the `PROCUREPULSE_URL` environment variable (default: `http://localhost:8000`).
3. Connect your incoming ERP webhook trigger (e.g. Airtable New Record or Google Sheet row).
4. Run a test execution to verify wave calls and PO writeback.
