# Voice Agent Workflow Replication Package

This repository contains anonymized templates, call-level data, and analysis scripts for a field deployment of AI-routed telephone service calls in three U.S. automotive repair shops. The materials are intended to reproduce the descriptive counts reported in the manuscript and to document the workflow templates at a reusable level.

## Repository Contents

### `call-data/`

- `study_332_calls.csv` contains 332 call records exported from the operational voice-agent platform. The file includes timing, duration, cost, disconnection reason, call status, platform sentiment, agent configuration label, redacted public log field, transcript text, and post-call analysis fields.

### `analysis-scripts/`

- `01_extract_transcripts.py` parses the consolidated CSV, extracts turn-level transcript structure, and writes portable JSON and CSV outputs under `analysis-output/` by default.
- `02_thematic_analysis.py` applies transparent keyword-based descriptive coding to the structured transcript output.
- `03_statistics_summary.py` reproduces aggregate and site-level descriptive statistics from the consolidated dataset.

### `voice-agent-templates/`

- `Auto_Repair_Template__After_Hours.retell.json` is a sanitized Retell AI export template. Tenant identifiers, webhook identifiers, shop-specific values, and private endpoints are represented with placeholders.

### `make-workflow-templates/`

- `Auto_Repair_Template__AI_Functions.blueprint.json` is a sanitized Make.com scenario blueprint for the AI function endpoints used by the voice agent.

### `n8n-workflow-templates/`

- `n8n_Workflow_Template__Records.json` is a sanitized n8n workflow template for post-call record creation and tool-call extraction.

### `All_Transcripts/`

This folder contains pseudonymized transcript files organized by anonymous site labels. These files are retained for auditability but are not required for reproducing the main descriptive counts, which are computed from `call-data/study_332_calls.csv`.

## Reproduce Main Counts

```bash
python analysis-scripts/03_statistics_summary.py
```

The command writes `analysis-output/descriptive_summary.json` and prints the main replication counts:

- total records: 332
- records with analyzable transcripts: 325
- successful calls: 234
- appointment activity: 113 true and 171 false among 284 nonmissing records
- platform sentiment counts: Neutral 240, Positive 81, Unknown 7, Negative 4

## Optional Pipeline

```bash
python analysis-scripts/01_extract_transcripts.py
python analysis-scripts/02_thematic_analysis.py
python analysis-scripts/03_statistics_summary.py
```

All scripts use paths relative to the repository root unless explicit paths are provided on the command line.

## Repository Checks

```bash
python -m pytest tests/test_repository_readiness.py
```

The checks guard against local absolute paths, author-identifying analysis metadata, stale account credentials, unredacted workflow account identifiers, and manuscript count regressions.

## Template Configuration

Before importing any workflow template into a live account, replace the placeholder names for auto repair shop, tow truck phone number, scheduling link, Make connection id, Twilio sender number, company id, and Supabase credential id with values from the destination account.

## Privacy Boundary

The repository uses anonymous site labels and placeholder contact details. Do not add real caller names, staff names, phone numbers, recording URLs, public log URLs, private endpoints, credentials, or shop-identifying metadata.
