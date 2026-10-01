#!/usr/bin/env python3
"""Score a formal review across every meeting, including zero-prediction runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owner_set(value: str | list[str]) -> set[str]:
    if isinstance(value, list):
        return {item.strip() for item in value if item.strip()}
    return {item.strip() for item in value.split(";") if item.strip()}


def divide(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=ROOT / "data/labels/final_gold_labels.csv")
    parser.add_argument("--allow-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    split = payload["run"]["split"]
    if split == "test" and not args.allow_test:
        raise SystemExit("REFUSED: formal test scoring requires --allow-test")
    meeting_ids = [row["transcript_id"] for row in payload["results"]]
    if len(meeting_ids) != len(set(meeting_ids)):
        raise ValueError("Prediction payload contains duplicate meetings")

    predictions = {}
    meeting_prediction_counts = {meeting_id: 0 for meeting_id in meeting_ids}
    for result in payload["results"]:
        meeting_id = result["transcript_id"]
        for number, item in enumerate(result["action_items"], start=1):
            prediction_id = f"{meeting_id}-P{number:03d}"
            predictions[prediction_id] = item
            meeting_prediction_counts[meeting_id] += 1

    with args.gold.open(newline="", encoding="utf-8-sig") as handle:
        gold = {row["action_id"]: row for row in csv.DictReader(handle) if row["transcript_id"] in meeting_ids}
    with args.review.open(newline="", encoding="utf-8-sig") as handle:
        review_rows = list(csv.DictReader(handle))
    if {row["prediction_id"] for row in review_rows} != set(predictions):
        raise ValueError("Review rows must cover every accepted prediction exactly once")

    matched_gold = set()
    tp = fp = 0
    owner_correct = owner_eligible = 0
    deadline_correct = deadline_eligible = 0
    owner_hallucinations = owner_null_cases = 0
    deadline_hallucinations = deadline_null_cases = 0
    counts = {
        meeting_id: {"tp": 0, "fp": 0, "gold": 0, "predictions": meeting_prediction_counts[meeting_id]}
        for meeting_id in meeting_ids
    }
    for row in gold.values():
        counts[row["transcript_id"]]["gold"] += 1

    for row in review_rows:
        prediction_id = row["prediction_id"]
        prediction = predictions[prediction_id]
        meeting_id = row["transcript_id"]
        decision = row["human_decision"].strip()
        if decision not in {"match", "no_match"}:
            raise ValueError(f"{prediction_id}: decision must be match or no_match")
        if not row["human_reason"].strip():
            raise ValueError(f"{prediction_id}: human_reason is required")
        if decision == "no_match":
            if row["final_gold_action_id"].strip():
                raise ValueError(f"{prediction_id}: no_match cannot carry a gold ID")
            fp += 1
            counts[meeting_id]["fp"] += 1
            continue

        gold_id = row["final_gold_action_id"].strip()
        if gold_id not in gold:
            raise ValueError(f"{prediction_id}: unknown gold ID {gold_id!r}")
        if gold_id in matched_gold:
            raise ValueError(f"Gold action {gold_id} matched more than once")
        if gold[gold_id]["transcript_id"] != meeting_id:
            raise ValueError(f"{prediction_id}: cross-meeting match is prohibited")
        matched_gold.add(gold_id)
        tp += 1
        counts[meeting_id]["tp"] += 1

        gold_owners = owner_set(gold[gold_id]["owner"])
        predicted_owners = owner_set(prediction["owners"])
        if gold_owners:
            owner_eligible += 1
            owner_correct += predicted_owners == gold_owners
        else:
            owner_null_cases += 1
            owner_hallucinations += bool(predicted_owners)

        gold_deadline = gold[gold_id]["deadline_text"].strip().casefold()
        predicted_deadline = (prediction.get("deadline_text") or "").strip().casefold()
        if gold_deadline:
            deadline_eligible += 1
            deadline_correct += predicted_deadline == gold_deadline
        else:
            deadline_null_cases += 1
            deadline_hallucinations += bool(predicted_deadline)

    fn = len(gold) - len(matched_gold)
    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    micro_f1 = divide(2 * tp, 2 * tp + fp + fn)
    per_meeting = {}
    defined_f1 = []
    for meeting_id in meeting_ids:
        row = counts[meeting_id]
        meeting_fn = row["gold"] - row["tp"]
        p = divide(row["tp"], row["tp"] + row["fp"])
        r = divide(row["tp"], row["gold"])
        f1 = divide(2 * row["tp"], 2 * row["tp"] + row["fp"] + meeting_fn)
        if f1 is not None:
            defined_f1.append(f1)
        per_meeting[meeting_id] = {
            **row,
            "fn": meeting_fn,
            "precision": p,
            "recall": r,
            "f1": f1,
        }

    output = {
        "evaluation": {
            "split": split,
            "system_version": payload["run"]["version"],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "matching": "human one-to-one semantic task review; owner and deadline scored separately",
            "meeting_scope": "all meetings in the prediction payload, including zero-prediction and invalid runs",
            "invalid_output_policy": payload["run"].get("invalid_output_policy"),
            "macro_policy": "exclude only meetings where both gold and predictions are zero because F1 is undefined",
            "predictions_sha256": sha256(args.predictions),
            "review_sha256": sha256(args.review),
            "gold_sha256": sha256(args.gold),
        },
        "task_detection": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "micro_precision": precision,
            "micro_recall": recall,
            "micro_f1": micro_f1,
            "macro_f1": sum(defined_f1) / len(defined_f1) if defined_f1 else None,
            "macro_defined_meetings": len(defined_f1),
        },
        "fields_on_matched_actions": {
            "owner_exact_correct": owner_correct,
            "owner_exact_eligible": owner_eligible,
            "owner_exact_accuracy": divide(owner_correct, owner_eligible),
            "deadline_exact_correct": deadline_correct,
            "deadline_exact_eligible": deadline_eligible,
            "deadline_exact_accuracy": divide(deadline_correct, deadline_eligible),
            "hallucinated_owner_count": owner_hallucinations,
            "null_owner_cases": owner_null_cases,
            "hallucinated_owner_rate": divide(owner_hallucinations, owner_null_cases),
            "hallucinated_deadline_count": deadline_hallucinations,
            "null_deadline_cases": deadline_null_cases,
            "hallucinated_deadline_rate": divide(deadline_hallucinations, deadline_null_cases),
        },
        "reliability": {
            "meeting_count": payload["run"]["meeting_count"],
            "valid_meeting_count": payload["run"].get("valid_meeting_count", payload["run"]["meeting_count"]),
            "invalid_meeting_count": payload["run"].get("invalid_meeting_count", 0),
            "validation_success_rate": payload["run"].get("validation_success_rate", 1.0),
            "retry_count": payload["run"].get("retry_count", 0),
            "estimated_cost_usd": payload["run"].get("estimated_cost_usd", 0.0),
        },
        "per_meeting": per_meeting,
        "matched_gold_action_ids": sorted(matched_gold),
        "unmatched_gold_action_ids": sorted(set(gold) - matched_gold),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"TP={tp} FP={fp} FN={fn} P={precision:.3f} R={recall:.3f} F1={micro_f1:.3f}")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
