"""Count actionable outcomes from executed agent tool calls.

An "actionable outcome" is a call in which the agent EXECUTED at least one
action tool that produced a concrete next step for the shop or caller. Evidence
is the platform's own tool-invocation log in the 'Transcript With Tool Calls'
column (only the tool names are read; argument values are redacted in the
shared data and are not needed for the count).

Action tools (mapped to the manuscript's outcome categories):
    appointment_link     -> scheduling link sent
    appointment_request  -> appointment request forwarded
    quote                -> quote request forwarded
    message              -> message recorded
    urgent_message       -> urgent notification dispatched
    contactTow           -> towing notification dispatched

Routing/utility tools are NOT counted: end_call, transfer_call, transition_to_*.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "call-data" / "study_332_calls.csv"
DEFAULT_OUTPUT_DIR = ROOT / "analysis-output"

ACTION_TOOLS = [
    "appointment_link",
    "appointment_request",
    "quote",
    "message",
    "urgent_message",
    "contactTow",
]

csv.field_size_limit(10 ** 7)


def load_rows(path):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def executed_tools(row):
    """Return the set of tool names invoked in a call."""
    raw = row.get("Transcript With Tool Calls", "")
    names = set()
    if raw and raw.strip():
        try:
            for entry in json.loads(raw):
                if entry.get("role") == "tool_call_invocation":
                    names.add(entry.get("name", ""))
        except json.JSONDecodeError:
            pass
    return names


def analyse(rows):
    transcripts = [r for r in rows if (r.get("Transcript") or "").strip()]
    per_tool = Counter()
    actionable = 0
    multi_category = 0
    records = []
    for row in transcripts:
        tools = executed_tools(row)
        fired = [t for t in ACTION_TOOLS if t in tools]
        for t in fired:
            per_tool[t] += 1
        is_actionable = len(fired) > 0
        actionable += is_actionable
        if len(fired) >= 2:
            multi_category += 1
        records.append({
            "call_id": row.get("Call ID", ""),
            "actionable_outcome": int(is_actionable),
            "n_categories": len(fired),
            **{f"tool_{t}": int(t in tools) for t in ACTION_TOOLS},
        })
    return transcripts, per_tool, actionable, multi_category, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    rows = load_rows(args.input)
    transcripts, per_tool, actionable, multi_category, records = analyse(rows)
    n = len(transcripts)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / "actionable_outcomes.csv"
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"Transcripts analysed: {n}")
    print("Per-category (distinct calls where the tool was executed):")
    for tool in ACTION_TOOLS:
        print(f"  {tool:20s} {per_tool[tool]:3d}")
    pct = 100 * actionable / n if n else 0
    print(f"Actionable outcomes (>=1 action tool executed): {actionable} ({pct:.1f}% of {n})")
    print(f"Calls counted in more than one category: {multi_category}")
    print(f"Per-call coding written to: {out_path}")


if __name__ == "__main__":
    main()
