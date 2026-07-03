"""Extract structured transcript records from the consolidated call CSV."""

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "call-data" / "study_332_calls.csv"
DEFAULT_OUTPUT_DIR = ROOT / "analysis-output"


def parse_transcript(raw_transcript):
    """Parse an Agent/User transcript string into turn dictionaries."""
    if not raw_transcript or not raw_transcript.strip():
        return []

    turns = []
    current_role = None
    current_text = []

    for line in raw_transcript.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Agent:"):
            if current_role is not None:
                turns.append({"role": current_role, "text": " ".join(current_text).strip()})
            current_role = "agent"
            current_text = [line[6:].strip()]
        elif line.startswith("User:"):
            if current_role is not None:
                turns.append({"role": current_role, "text": " ".join(current_text).strip()})
            current_role = "user"
            current_text = [line[5:].strip()]
        elif current_role is not None:
            current_text.append(line)

    if current_role is not None:
        turns.append({"role": current_role, "text": " ".join(current_text).strip()})
    return turns


def parse_duration_seconds(value):
    """Convert common call-duration strings to seconds."""
    value = (value or "").strip()
    if not value or ":" not in value:
        return None
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def parse_cost(value):
    """Parse a currency string into a float."""
    value = (value or "").strip().replace("$", "")
    return float(value) if value else 0.0


def site_from_agent_name(agent_name):
    """Extract the anonymous site label from the platform agent label."""
    match = re.match(r"(Shop_[ABC])\b", agent_name or "")
    return match.group(1) if match else "Unknown"


def count_turns(turns):
    """Return agent turn count and user turn count."""
    agent_turns = sum(1 for turn in turns if turn["role"] == "agent")
    user_turns = sum(1 for turn in turns if turn["role"] == "user")
    return agent_turns, user_turns


def count_words(turns, role=None):
    """Count words across all turns or only turns with a selected role."""
    return sum(
        len(turn["text"].split())
        for turn in turns
        if role is None or turn["role"] == role
    )


def detect_ai_disclosure(turns):
    """Detect whether the first agent turn discloses AI or automated identity."""
    first_agent = next((turn for turn in turns if turn["role"] == "agent"), None)
    if not first_agent:
        return False
    text = first_agent["text"].lower()
    return any(term in text for term in ("ai", "automated", "virtual assistant"))


def extract_records(input_path):
    """Load call rows and return structured replication records."""
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    records = []
    for row in rows:
        turns = parse_transcript(row.get("Transcript", ""))
        agent_turns, user_turns = count_turns(turns)
        agent_words = count_words(turns, "agent")
        user_words = count_words(turns, "user")
        records.append(
            {
                "site": site_from_agent_name(row.get("Agent Name", "")),
                "call_id": row.get("Call ID", ""),
                "timestamp": row.get("Time", ""),
                "duration_sec": parse_duration_seconds(row.get("Call Duration", "")),
                "call_successful": row.get("Call Successful", ""),
                "disconnection_reason": row.get("Disconnection Reason", ""),
                "user_sentiment": row.get("User Sentiment", "Unknown") or "Unknown",
                "appointment_activity": row.get("appointment_activity", ""),
                "latency_ms": row.get("End to End Latency", ""),
                "cost": parse_cost(row.get("Cost", "")),
                "agent_name": row.get("Agent Name", ""),
                "num_turns_total": agent_turns + user_turns,
                "num_agent_turns": agent_turns,
                "num_user_turns": user_turns,
                "agent_word_count": agent_words,
                "user_word_count": user_words,
                "total_word_count": agent_words + user_words,
                "ai_disclosure_detected": detect_ai_disclosure(turns),
                "transcript_turns": turns,
            }
        )
    return records


def write_outputs(records, output_dir):
    """Write structured JSON and a transcript-free summary CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "all_calls_structured.json"
    json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_path = output_dir / "all_calls_summary.csv"
    fields = [
        "site",
        "call_id",
        "timestamp",
        "duration_sec",
        "call_successful",
        "disconnection_reason",
        "user_sentiment",
        "appointment_activity",
        "latency_ms",
        "cost",
        "num_turns_total",
        "num_agent_turns",
        "num_user_turns",
        "agent_word_count",
        "user_word_count",
        "total_word_count",
        "ai_disclosure_detected",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record[field] for field in fields})
    return json_path, csv_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    records = extract_records(args.input)
    json_path, csv_path = write_outputs(records, args.output_dir)
    with_transcript = sum(1 for record in records if record["num_turns_total"] > 0)

    print(f"Total records: {len(records)}")
    print(f"Records with transcript turns: {with_transcript}")
    print(f"Structured JSON: {json_path}")
    print(f"Summary CSV: {csv_path}")


if __name__ == "__main__":
    main()
