"""Apply transparent keyword-based descriptive coding to structured calls."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "analysis-output" / "all_calls_structured.json"
DEFAULT_OUTPUT_DIR = ROOT / "analysis-output"


CODEBOOK = {
    "appointment_request": ["appointment", "schedule", "book", "bring in", "come in"],
    "quote_request": ["quote", "estimate", "how much", "price", "cost"],
    "towing_request": ["tow", "towing", "broke down", "stranded"],
    "message_request": ["message", "tell them", "let them know", "call me back"],
    "hours_or_dropoff": ["hours", "closed", "after hours", "drop off", "drop-off"],
    "human_request": ["real person", "human", "representative", "speak to someone"],
    "frustration_marker": ["frustrated", "annoying", "ridiculous", "not helpful"],
    "gratitude_marker": ["thank", "thanks", "appreciate", "great", "perfect"],
}


def user_text(call):
    """Concatenate user turns for keyword coding."""
    return " ".join(
        turn.get("text", "").lower()
        for turn in call.get("transcript_turns", [])
        if turn.get("role") == "user"
    )


def code_call(call):
    """Return binary keyword codes for one call."""
    text = user_text(call)
    codes = {
        code: any(keyword in text for keyword in keywords)
        for code, keywords in CODEBOOK.items()
    }
    return {
        "call_id": call.get("call_id", ""),
        "site": call.get("site", "Unknown"),
        "user_sentiment": call.get("user_sentiment", "Unknown"),
        "call_successful": call.get("call_successful", ""),
        "appointment_activity": call.get("appointment_activity", ""),
        **codes,
    }


def analyse_calls(calls):
    """Code calls that contain at least one transcript turn."""
    return [code_call(call) for call in calls if call.get("num_turns_total", 0) > 0]


def summarize_codes(results):
    """Aggregate keyword-code frequencies."""
    summary = Counter()
    for result in results:
        for code in CODEBOOK:
            if result[code]:
                summary[code] += 1
    return dict(summary)


def write_outputs(results, summary, output_dir):
    """Write coding outputs as JSON and CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "thematic_analysis_results.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    summary_path = output_dir / "thematic_code_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    csv_path = output_dir / "thematic_analysis_summary.csv"
    fields = [
        "call_id",
        "site",
        "user_sentiment",
        "call_successful",
        "appointment_activity",
        *CODEBOOK.keys(),
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    return json_path, summary_path, csv_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    calls = json.loads(args.input.read_text(encoding="utf-8"))
    results = analyse_calls(calls)
    summary = summarize_codes(results)
    json_path, summary_path, csv_path = write_outputs(results, summary, args.output_dir)

    print(f"Coded records: {len(results)}")
    print(f"Detailed output: {json_path}")
    print(f"Summary output: {summary_path}")
    print(f"CSV output: {csv_path}")


if __name__ == "__main__":
    main()
