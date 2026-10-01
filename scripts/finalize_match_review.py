#!/usr/bin/env python3
"""Validate a completed human match review and write reproducible metrics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from actionai.evaluation import score_review  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=ROOT / "data/labels/final_gold_labels.csv")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    if payload["run"]["split"] == "test" and not args.allow_test:
        print("REFUSED: test scoring requires --allow-test after the formal freeze gate.", file=sys.stderr)
        return 2

    predictions = {}
    for result in payload["results"]:
        for number, item in enumerate(result["action_items"], start=1):
            predictions[f"{result['transcript_id']}-P{number:03d}"] = item
    with args.gold.open(newline="", encoding="utf-8-sig") as handle:
        gold = {row["action_id"]: row for row in csv.DictReader(handle)}
    with args.review.open(newline="", encoding="utf-8-sig") as handle:
        review_rows = list(csv.DictReader(handle))
    if {row["prediction_id"] for row in review_rows} != set(predictions):
        raise ValueError("Review rows must cover every prediction exactly once")

    metrics = score_review(predictions, gold, review_rows)
    output = {
        "evaluation": {
            "split": payload["run"]["split"],
            "system_version": payload["run"]["version"],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "matching": "human one-to-one semantic review; owner and deadline scored separately",
            "predictions_sha256": sha256(args.predictions),
            "review_sha256": sha256(args.review),
            "gold_sha256": sha256(args.gold),
        },
        **metrics,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    task = metrics["task_detection"]
    print(
        f"TP={task['tp']} FP={task['fp']} FN={task['fn']} "
        f"P={task['micro_precision']:.3f} R={task['micro_recall']:.3f} F1={task['micro_f1']:.3f}"
    )
    print(f"Wrote metrics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

