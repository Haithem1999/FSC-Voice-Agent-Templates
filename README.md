# FSC-Project — Voice Agent & Workflow Templates

This repository contains the blueprint **templates** used to build the production voice agents and their associated automation workflows for the three auto repair shops studied in the thesis (Shop_A, Shop_B, and Shop_C). The templates here are sanitised, shop-agnostic versions intended for reuse and reproducibility, with placeholders (e.g. `[AUTO REPAIR SHOP]`, `[TOW TRUCK PHONE NUMBER]`, `[SCHEDULING LINK]`) marking the values that must be configured per shop.

## Repository Contents

### `voice-agent-templates/`
Retell AI agent export template (JSON). Defines the voice agent's general prompt, multi-state finite state machine, function-calling tools, voice/language settings, and post-call analysis configuration.

- `Auto_Repair_Template__After_Hours.retell.json` — After-hours agent (Chloe) covering common inquiries, appointments, quote requests, urgent messages, tows, and message-taking.

### `make-workflow-templates/`
Make.com scenario export template (JSON blueprint). Implements the AI function endpoints invoked by the voice agent via webhooks.

- `Auto_Repair_Template__AI_Functions.blueprint.json` — Webhook router with branches for leave-message, towing (notify tow company + SMS confirmation to user), quote request, and scheduling-link delivery, integrating SendGrid (email) and Twilio (SMS).

### `n8n-workflow-templates/`
n8n workflow export template (JSON). Implements the post-call analytics pipeline.

- `n8n_Workflow_Template__Records.json` — Receives Retell AI `call_analyzed` webhooks, filters for completed phone calls, writes a structured record into Supabase (call cost, duration, sentiment, transcript, recording URL, etc.), and detects tool-call usage from the transcript.

### `analysis-scripts/`
Python scripts used for the quantitative and qualitative analysis presented in Chapter 5 of the thesis.

- `01_extract_transcripts.py` — Parses the post-call CSV exports for all three shops, structures the transcripts turn-by-turn, extracts tool-call events, and emits a clean JSON/CSV dataset.
- `02_thematic_analysis.py` — Applies the hybrid deductive/inductive coding framework (Appendix A of the thesis) to the structured transcripts and produces per-call thematic coding results.
- `03_statistics_summary.py` — Consolidates the structured data and thematic results into the descriptive statistics, cross-tabulations, temporal analyses, and thesis-ready CSV tables (Chapter 5).

### `All_Transcripts/`
The full corpus of 332 after-hours call transcripts used as the empirical basis for Chapter 5, organised one file per call under a folder for each shop:

- `Shop_A/` — 148 transcripts
- `Shop_B/` — 117 transcripts
- `Shop_C/` — 67 transcripts

Each transcript file begins with call metadata (shop name, call ID, timestamp, duration, disconnection reason, sentiment, cost, end-to-end latency, agent name) followed by the turn-by-turn agent/user dialogue. Consistent with Appendix B of the thesis, caller names and phone numbers are retained as recorded by the system.

## Configuring the Templates

Before deploying the templates, replace the bracketed placeholders with shop-specific values:

| Placeholder                       | Description                                              |
|-----------------------------------|----------------------------------------------------------|
| `[AUTO REPAIR SHOP]`              | Shop name                                                |
| `[SHOP FULL ADDRESS]`             | Shop street address                                      |
| `[SHOP HOURS OF OPERATION]`       | Hours per day of week                                    |
| `[TOW TRUCK COMPANY]`             | Preferred tow partner name                               |
| `[TOW TRUCK PHONE NUMBER]`        | Tow partner phone (used in SMS body and dispatch)        |
| `[SCHEDULING LINK]`               | Online booking URL sent to callers                       |
| `[INSERT IANA Time Zone Identifier]` | e.g. `America/Los_Angeles`                             |
| `shop@example.com` (Make blueprint) | Shop notification email address                        |
| `company_id` (n8n workflow)       | Internal identifier for the shop in Supabase             |

The Retell, Make, and Twilio connection IDs in the JSON exports are tenant-specific and must be re-bound to the destination account when importing.

## License & Use

These templates are provided for academic and educational purposes alongside the thesis. Connections, credentials, and shop-specific copy have been removed or replaced with placeholders.
