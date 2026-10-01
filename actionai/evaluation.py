"""Transparent scoring helpers for human-adjudicated action matches."""

from __future__ import annotations

from statistics import mean
from typing import Any


def normalise_owner_set(value: str | list[str]) -> set[str]:
    if isinstance(value, list):
        return {item.strip() for item in value if item.strip()}
    return {item.strip() for item in value.split(";") if item.strip()}


def safe_divide(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score_review(
    predictions: dict[str, dict[str, Any]],
    gold: dict[str, dict[str, str]],
    review_rows: list[dict[str, str]],
) -> dict[str, Any]:
    matched_gold: set[str] = set()
    tp = fp = owner_correct = owner_eligible = 0
    deadline_correct = deadline_eligible = 0
    owner_hallucinations = owner_null_cases = 0
    deadline_hallucinations = deadline_null_cases = 0
    by_meeting: dict[str, dict[str, int]] = {}

    for row in review_rows:
        prediction_id = row["prediction_id"]
        prediction = predictions[prediction_id]
        meeting_id = row["transcript_id"]
        counts = by_meeting.setdefault(meeting_id, {"tp": 0, "fp": 0, "gold": 0})
        decision = row["human_decision"].strip()
        if decision not in {"match", "no_match"}:
            raise ValueError(f"{prediction_id}: human_decision must be match or no_match")
        if not row["human_reason"].strip():
            raise ValueError(f"{prediction_id}: human_reason is required")
        if decision == "no_match":
            if row["final_gold_action_id"].strip():
                raise ValueError(f"{prediction_id}: no_match cannot have a gold action ID")
            fp += 1
            counts["fp"] += 1
            continue

        gold_id = row["final_gold_action_id"].strip()
        if gold_id not in gold:
            raise ValueError(f"{prediction_id}: unknown gold action {gold_id!r}")
        if gold_id in matched_gold:
            raise ValueError(f"Gold action {gold_id} was matched more than once")
        if gold[gold_id]["transcript_id"] != meeting_id:
            raise ValueError(f"{prediction_id}: cross-transcript match is prohibited")
        matched_gold.add(gold_id)
        tp += 1
        counts["tp"] += 1

        gold_owners = normalise_owner_set(gold[gold_id]["owner"])
        predicted_owners = normalise_owner_set(prediction["owners"])
        if gold_owners:
            owner_eligible += 1
            owner_correct += predicted_owners == gold_owners
        else:
            owner_null_cases += 1
            owner_hallucinations += bool(predicted_owners)

        gold_deadline = gold[gold_id]["deadline_text"].strip().casefold()
        predicted_deadline = (prediction["deadline_text"] or "").strip().casefold()
        if gold_deadline:
            deadline_eligible += 1
            deadline_correct += predicted_deadline == gold_deadline
        else:
            deadline_null_cases += 1
            deadline_hallucinations += bool(predicted_deadline)

    relevant_gold = {
        gold_id: row for gold_id, row in gold.items() if row["transcript_id"] in by_meeting
    }
    for row in relevant_gold.values():
        by_meeting[row["transcript_id"]]["gold"] += 1
    fn = len(relevant_gold) - len(matched_gold)
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else 0.0

    per_meeting = {}
    macro_values = []
    for meeting_id, counts in sorted(by_meeting.items()):
        meeting_fn = counts["gold"] - counts["tp"]
        p = safe_divide(counts["tp"], counts["tp"] + counts["fp"])
        r = safe_divide(counts["tp"], counts["tp"] + meeting_fn)
        meeting_f1 = (2 * p * r / (p + r)) if p and r else 0.0
        macro_values.append(meeting_f1)
        per_meeting[meeting_id] = {**counts, "fn": meeting_fn, "precision": p, "recall": r, "f1": meeting_f1}

    return {
        "task_detection": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "micro_precision": precision,
            "micro_recall": recall,
            "micro_f1": f1,
            "macro_f1": mean(macro_values) if macro_values else None,
        },
        "fields_on_matched_actions": {
            "owner_exact_correct": owner_correct,
            "owner_exact_eligible": owner_eligible,
            "owner_exact_accuracy": safe_divide(owner_correct, owner_eligible),
            "deadline_exact_correct": deadline_correct,
            "deadline_exact_eligible": deadline_eligible,
            "deadline_exact_accuracy": safe_divide(deadline_correct, deadline_eligible),
            "hallucinated_owner_count": owner_hallucinations,
            "null_owner_cases": owner_null_cases,
            "hallucinated_owner_rate": safe_divide(owner_hallucinations, owner_null_cases),
            "hallucinated_deadline_count": deadline_hallucinations,
            "null_deadline_cases": deadline_null_cases,
            "hallucinated_deadline_rate": safe_divide(deadline_hallucinations, deadline_null_cases),
        },
        "per_meeting": per_meeting,
        "matched_gold_action_ids": sorted(matched_gold),
        "unmatched_gold_action_ids": sorted(set(relevant_gold) - matched_gold),
    }

