#!/usr/bin/env python3
"""Prepare a human match-review sheet without declaring semantic matches final."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from actionai.rule_baseline import jaccard  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=ROOT / "data/labels/final_gold_labels.csv")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    split = payload["run"]["split"]
    if split == "test" and not args.allow_test:
        print("REFUSED: test matching review requires --allow-test after the formal freeze gate.", file=sys.stderr)
        return 2

    with args.gold.open(newline="", encoding="utf-8-sig") as handle:
        gold_rows = list(csv.DictReader(handle))
    gold_by_meeting: dict[str, list[dict[str, str]]] = {}
    for row in gold_rows:
        gold_by_meeting.setdefault(row["transcript_id"], []).append(row)

    output_rows: list[dict[str, str]] = []
    for result in payload["results"]:
        meeting_id = result["transcript_id"]
        meeting_gold = gold_by_meeting.get(meeting_id, [])
        for number, prediction in enumerate(result["action_items"], start=1):
            pred_ids = set(prediction.get("evidence_ids", []))
            ranked = []
            for gold in meeting_gold:
                gold_ids = {item.strip() for item in gold["evidence_ids"].split("|") if item.strip()}
                evidence_overlap = bool(pred_ids & gold_ids)
                score = 0.65 * jaccard(prediction["task"], gold["task"]) + 0.35 * evidence_overlap
                ranked.append((score, gold))
            ranked.sort(key=lambda item: item[0], reverse=True)
            best_score, best_gold = ranked[0] if ranked else (0.0, None)
            suggested = best_gold["action_id"] if best_gold and best_score >= 0.25 else ""
            output_rows.append(
                {
                    "transcript_id": meeting_id,
                    "prediction_id": f"{meeting_id}-P{number:03d}",
                    "predicted_task": prediction["task"],
                    "predicted_owners": "; ".join(prediction["owners"]),
                    "predicted_deadline": prediction["deadline_text"] or "",
                    "evidence_ids": "|".join(prediction["evidence_ids"]),
                    "rule_id": prediction.get("rule_id", "llm"),
                    "suggested_gold_action_id": suggested,
                    "suggestion_score": f"{best_score:.3f}",
                    "human_decision": "",
                    "final_gold_action_id": "",
                    "human_reason": "",
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0]) if output_rows else []
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} predictions for blind human review to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
