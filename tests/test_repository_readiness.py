import csv
import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readme_uses_anonymous_manuscript_scope():
    text = read_text("README.md").lower()
    forbidden = [
        "thesis",
        "chapter",
        "appendix",
        "full corpus of 332 after-hours",
        "gasmi",
        "haithem",
    ]
    for term in forbidden:
        assert term not in text
    assert "ai-routed telephone service calls" in text


def test_analysis_scripts_are_portable_and_anonymous():
    forbidden = [
        "Gasmi",
        "Haithem",
        "C:/Users",
        "Downloads",
        "Documents/thesis_analysis",
        "Thesis:",
        "thesis-ready",
        "thesis_tables",
    ]
    for script in sorted((ROOT / "analysis-scripts").glob("*.py")):
        text = script.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in text, f"{term} found in {script.name}"


def test_statistics_script_matches_consolidated_dataset_counts():
    stats = load_module("analysis-scripts/03_statistics_summary.py", "stats_summary")
    data_path = ROOT / "call-data" / "study_332_calls.csv"
    rows = list(csv.DictReader(data_path.open(encoding="utf-8")))

    assert stats.count_successful_calls(rows) == 234
    assert stats.count_calls_with_transcript(rows) == 325
    assert stats.count_appointment_activity(rows) == (113, 171)
    assert stats.count_sentiment(rows) == {
        "Neutral": 240,
        "Positive": 81,
        "Unknown": 7,
        "Negative": 4,
    }


def test_workflow_templates_do_not_expose_account_metadata():
    n8n = json.loads(read_text("n8n-workflow-templates/n8n_Workflow_Template__Records.json"))
    n8n_text = json.dumps(n8n)
    for term in ["bT9E8cRE5l43ZnjK", "AI_Platform_DB", "automod-racing"]:
        assert term not in n8n_text
    assert "[COMPANY_ID]" in n8n_text
    assert "[SUPABASE_CREDENTIAL_ID]" in n8n_text

    make_text = read_text("make-workflow-templates/Auto_Repair_Template__AI_Functions.blueprint.json")
    for phone in ["+13802255538", "+18777130763"]:
        assert phone not in make_text
    assert not re.search(r'"__IMTCONN__"\s*:\s*\d+', make_text)
    assert "[TWILIO_FROM_NUMBER]" in make_text
    assert "[MAKE_CONNECTION_ID]" in make_text


def test_retell_template_uses_placeholder_metadata():
    text = read_text("voice-agent-templates/Auto_Repair_Template__After_Hours.retell.json")
    for term in [
        "llm_b6b5d08aa178bee1e2c11bb0d6b7",
        "643194b8-f68a-4ebe-b94a-9f0052b586f7",
    ]:
        assert term not in text
    assert "[RETELL_LLM_ID]" in text
    assert "https://n8n.example.com/webhook/[WEBHOOK_ID]" in text
