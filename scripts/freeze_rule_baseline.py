#!/usr/bin/env python3
"""Record immutable hashes for the confirmed ActionAI rule baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "configs/RULE_BASELINE_VERSION.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = ROOT / "configs/rule_baseline_v1.json"
    implementation_path = ROOT / "actionai/rule_baseline.py"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    if config["version"] != "rule-baseline-v1.0-frozen":
        raise ValueError("Configuration version is not frozen")
    if predictions["run"]["version"] != config["version"]:
        raise ValueError("Prediction and configuration versions disagree")
    if predictions["run"]["split"] != "development":
        raise ValueError("Freeze evidence must come from development only")
    if metrics["evaluation"]["split"] != "development":
        raise ValueError("Freeze metrics must come from development only")

    files = {
        "config": config_path,
        "implementation": implementation_path,
        "development_predictions": args.predictions.resolve(),
        "human_match_review": args.review.resolve(),
        "development_metrics": args.metrics.resolve(),
        "locked_gold_labels": ROOT / "data/labels/final_gold_labels.csv",
    }
    payload = {
        "version": config["version"],
        "status": "frozen_before_test",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "development_meetings": ["ES2003a", "ES2003b", "ES2003c"],
        "test_outputs_seen": False,
        "change_policy": "Any change requires a new version and a complete rerun of every affected arm.",
        "files": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for name, path in files.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {config['version']} in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
