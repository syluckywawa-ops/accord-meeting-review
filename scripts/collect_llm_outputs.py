#!/usr/bin/env python3
"""Collect validated per-meeting LLM logs into the common evaluation format."""

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
    parser.add_argument("--split", choices=("development", "test"), default="development")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/data_manifest.csv")
    parser.add_argument("--transcript-dir", type=Path, default=ROOT / "data/derived/transcripts")
    parser.add_argument("--metadata-dir", type=Path, default=ROOT / "data/derived/metadata")
    parser.add_argument("--prompt-dir", type=Path, default=ROOT / "prompts")
    parser.add_argument("--allow-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.input_dir = args.input_dir.resolve()
    args.output = args.output.resolve()
    args.manifest = args.manifest.resolve()
    args.transcript_dir = args.transcript_dir.resolve()
    args.metadata_dir = args.metadata_dir.resolve()
    args.prompt_dir = args.prompt_dir.resolve()
    if args.split == "test" and not args.allow_test:
        print("REFUSED: test collection requires --allow-test after formal execution.", file=sys.stderr)
        return 2
    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        meetings = [row for row in csv.DictReader(handle) if row["split"] == args.split]

    results = []
    config_versions = set()
    config_hashes = set()
    schema_hashes = set()
    total_cost = 0.0
    total_retries = 0
    for row in meetings:
        meeting_id = row["meeting_id"]
        path = args.input_dir / f"{meeting_id}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        record = json.loads(path.read_text(encoding="utf-8"))
        run = record["run"]
        if run["condition"] != args.condition or run["split"] != args.split or run["meeting_id"] != meeting_id:
            raise ValueError(f"Run metadata mismatch in {path}")
        if record["status"] != "valid":
            raise ValueError(f"Cannot collect invalid output {path}")
        transcript = (args.transcript_dir / f"{meeting_id}.txt").read_text(encoding="utf-8")
        metadata = json.loads((args.metadata_dir / f"{meeting_id}.json").read_text(encoding="utf-8"))
        messages = build_messages(
            condition=args.condition,
            meeting_id=meeting_id,
            meeting_date=metadata.get("date") or "",
            transcript=transcript,
            prompt_dir=args.prompt_dir,
        )
        if canonical_hash(messages) != run["prompt_hash"]:
            raise ValueError(f"Current prompt assets do not reproduce prompt hash for {meeting_id}")
        config_versions.add(run["config_version"])
        config_hashes.add(run["config_sha256"])
        schema_hashes.add(run["schema_sha256"])
        total_cost += record["usage_total"]["estimated_cost_usd"]
        total_retries += record["retry_count"]
        results.append(
            {
                "transcript_id": meeting_id,
                "raw_log_path": str(path.relative_to(ROOT)),
                "raw_log_sha256": sha256(path),
                "action_items": record["parsed_output"]["action_items"],
            }
        )
    if len(config_versions) != 1 or len(config_hashes) != 1 or len(schema_hashes) != 1:
        raise ValueError("Collected runs do not share one configuration and schema")

    prompt_files = [
        args.prompt_dir / "system_v1.txt",
        args.prompt_dir / "user_template_v1.txt",
        args.prompt_dir / "few_shot_examples_v1.json",
    ]
    payload = {
        "run": {
            "system": "structured LLM",
            "version": next(iter(config_versions)),
            "condition": args.condition,
            "split": args.split,
            "meeting_count": len(results),
            "config_sha256": next(iter(config_hashes)),
            "schema_sha256": next(iter(schema_hashes)),
            "prompt_asset_sha256": {path.name: sha256(path) for path in prompt_files},
            "retry_count": total_retries,
            "estimated_cost_usd": total_cost,
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Collected {sum(len(row['action_items']) for row in results)} predictions from {len(results)} meetings")
    print(f"Retries={total_retries}, estimated cost=${total_cost:.4f}, output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
