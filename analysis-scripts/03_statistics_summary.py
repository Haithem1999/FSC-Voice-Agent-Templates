"""Reproduce descriptive statistics from the consolidated call dataset."""

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "call-data" / "study_332_calls.csv"
DEFAULT_OUTPUT_DIR = ROOT / "analysis-output"


def normalize_bool(value):
    """Normalize common boolean-like strings."""
    return (value or "").strip().lower()


def is_successful(row):
    """Return True when the platform marks the call as successful."""
    return normalize_bool(row.get("Call Successful")) in {"successful", "true", "yes", "1"}


def count_successful_calls(rows):
    """Count successful calls in raw CSV rows."""
    return sum(1 for row in rows if is_successful(row))


def count_calls_with_transcript(rows):
    """Count rows with non-empty transcript text."""
    return sum(1 for row in rows if (row.get("Transcript") or "").strip())


def count_appointment_activity(rows):
    """Return true and false counts for nonmissing appointment activity."""
    true_count = 0
    false_count = 0
    for row in rows:
        value = normalize_bool(row.get("appointment_activity"))
        if value == "true":
            true_count += 1
        elif value == "false":
            false_count += 1
    return true_count, false_count


def count_sentiment(rows):
    """Count platform-generated sentiment labels."""
    return dict(Counter((row.get("User Sentiment") or "Unknown").strip() or "Unknown" for row in rows))


def parse_duration_seconds(value):
    """Convert call-duration strings to seconds."""
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


def site_label(row):
    """Extract the anonymous site label from the platform agent label."""
    agent_name = row.get("Agent Name", "") or ""
    if agent_name.startswith("Shop_A"):
        return "Site A"
    if agent_name.startswith("Shop_B"):
        return "Site B"
    if agent_name.startswith("Shop_C"):
        return "Site C"
    return "Unknown"


def safe_mean(values):
    """Return mean or zero for an empty list."""
    return statistics.mean(values) if values else 0.0


def summarize_rows(rows):
    """Compute aggregate and site-level descriptive statistics."""
    summaries = {}
    groups = defaultdict(list)
    groups["Aggregate"] = rows
    for row in rows:
        groups[site_label(row)].append(row)

    for label in ["Site A", "Site B", "Site C", "Aggregate"]:
        subset = groups[label]
        durations = [
            duration
            for duration in (parse_duration_seconds(row.get("Call Duration")) for row in subset)
            if duration is not None
        ]
        costs = [parse_cost(row.get("Cost")) for row in subset]
        appointment_true, appointment_false = count_appointment_activity(subset)
        appointment_denominator = appointment_true + appointment_false
        summaries[label] = {
            "total_records": len(subset),
            "records_with_transcript": count_calls_with_transcript(subset),
            "successful_calls": count_successful_calls(subset),
            "completion_rate_percent": round(count_successful_calls(subset) / len(subset) * 100, 1)
            if subset else 0.0,
            "appointment_activity_true": appointment_true,
            "appointment_activity_false": appointment_false,
            "appointment_activity_denominator": appointment_denominator,
            "appointment_activity_rate_percent": round(appointment_true / appointment_denominator * 100, 1)
            if appointment_denominator else 0.0,
            "sentiment": count_sentiment(subset),
            "duration_seconds_mean": round(safe_mean(durations), 1),
            "duration_seconds_median": round(statistics.median(durations), 1) if durations else 0.0,
            "cost_total_usd": round(sum(costs), 3),
            "cost_mean_usd": round(safe_mean(costs), 3),
        }
    return summaries


def load_rows(input_path):
    """Load consolidated CSV rows."""
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_summary(summary, output_dir):
    """Write the descriptive summary JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "descriptive_summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    rows = load_rows(args.input)
    summary = summarize_rows(rows)
    output_path = write_summary(summary, args.output_dir)
    aggregate = summary["Aggregate"]

    print(f"Total records: {aggregate['total_records']}")
    print(f"Records with transcripts: {aggregate['records_with_transcript']}")
    print(f"Successful calls: {aggregate['successful_calls']}")
    print(
        "Appointment activity: "
        f"{aggregate['appointment_activity_true']} true, "
        f"{aggregate['appointment_activity_false']} false"
    )
    print(f"Sentiment counts: {aggregate['sentiment']}")
    print(f"Observed platform usage cost: ${aggregate['cost_total_usd']:.2f}")
    print(f"Summary JSON: {output_path}")


if __name__ == "__main__":
    main()
