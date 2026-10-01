#!/usr/bin/env python3
"""Collect frozen formal LLM logs, treating invalid outputs as no accepted predictions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from actionai.llm_pipeline import canonical_hash  # noqa: E402
from actionai.prompts import build_messages  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=("zero_shot", "few_shot"), required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/data_manifest.csv")
    parser.add_argument("--transcript-dir", type=Path, default=ROOT / "data/derived/transcripts")
    parser.add_argument("--metadata-dir", type=Path, default=ROOT / "data/derived/metadata")
    parser.add_argument("--prompt-dir", type=Path, default=ROOT / "prompts")
    parser.add_argument("--frozen-config", type=Path, default=ROOT / "configs/llm_experiment_v1_frozen.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = {
        name: path.resolve()
        for name, path in vars(args).items()
        if isinstance(path, Path)
    }
    with paths["manifest"].open(newline="", encoding="utf-8-sig") as handle:
        meetings = [row for row in csv.DictReader(handle) if row["split"] == "test"]
    config = json.loads(paths["frozen_config"].read_text(encoding="utf-8"))
    expected_config_hash = sha256(paths["frozen_config"])

    results = []
    invalid_runs = []
    total_cost = 0.0
    total_retries = 0
    config_hashes = set()
    schema_hashes = set()
    for row in meetings:
        meeting_id = row["meeting_id"]
        path = paths["input_dir"] / f"{meeting_id}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        record = json.loads(path.read_text(encoding="utf-8"))
        run = record["run"]
        if run["condition"] != args.condition or run["split"] != "test" or run["meeting_id"] != meeting_id:
            raise ValueError(f"Run metadata mismatch in {path}")
        if run["config_version"] != config["version"] or run["config_sha256"] != expected_config_hash:
            raise ValueError(f"Frozen configuration mismatch in {path}")
        transcript = (paths["transcript_dir"] / f"{meeting_id}.txt").read_text(encoding="utf-8")
        metadata = json.loads((paths["metadata_dir"] / f"{meeting_id}.json").read_text(encoding="utf-8"))
        messages = build_messages(
            condition=args.condition,
            meeting_id=meeting_id,
            meeting_date=metadata.get("date") or "",
            transcript=transcript,
            prompt_dir=paths["prompt_dir"],
        )
        if canonical_hash(messages) != run["prompt_hash"]:
            raise ValueError(f"Frozen prompt assets do not reproduce prompt hash for {meeting_id}")
        config_hashes.add(run["config_sha256"])
        schema_hashes.add(run["schema_sha256"])
        total_cost += record["usage_total"]["estimated_cost_usd"]
        total_retries += record["retry_count"]
        accepted = record["parsed_output"]["action_items"] if record["status"] == "valid" else []
        results.append(
            {
                "transcript_id": meeting_id,
                "run_status": record["status"],
                "raw_log_path": str(path.relative_to(ROOT)),
                "raw_log_sha256": sha256(path),
                "action_items": accepted,
            }
        )
        if record["status"] != "valid":
            last_attempt = record["attempts"][-1]
            invalid_runs.append(
                {
                    "transcript_id": meeting_id,
                    "retry_count": record["retry_count"],
                    "parsed_action_count": len(record["parsed_output"]["action_items"]),
                    "final_validation_issues": last_attempt.get("validation_issues", []),
                    "scoring_treatment": "no accepted predictions; gold actions remain unmatched",
                }
            )
    if len(config_hashes) != 1 or len(schema_hashes) != 1:
        raise ValueError("Formal logs do not share one frozen configuration and schema")

    payload = {
        "run": {
            "system": "structured LLM",
            "version": config["version"],
            "condition": args.condition,
            "split": "test",
            "meeting_count": len(results),
            "valid_meeting_count": sum(row["run_status"] == "valid" for row in results),
            "invalid_meeting_count": len(invalid_runs),
            "validation_success_rate": sum(row["run_status"] == "valid" for row in results) / len(results),
            "config_sha256": next(iter(config_hashes)),
            "schema_sha256": next(iter(schema_hashes)),
            "retry_count": total_retries,
            "estimated_cost_usd": total_cost,
            "invalid_output_policy": "Invalid after one repair contributes no accepted predictions to primary scoring.",
        },
        "results": results,
        "invalid_runs": invalid_runs,
    }
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Collected {sum(len(row['action_items']) for row in results)} accepted predictions; "
        f"valid={payload['run']['valid_meeting_count']}, invalid={payload['run']['invalid_meeting_count']}, "
        f"cost=${total_cost:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
