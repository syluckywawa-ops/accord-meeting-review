#!/usr/bin/env python3
"""Run zero-shot or few-shot ActionAI extraction with complete audit logs."""

from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openai import OpenAI  # noqa: E402

from actionai.llm_pipeline import canonical_hash, execute_extraction  # noqa: E402
from actionai.output_validation import validate_complete_input  # noqa: E402
from actionai.prompts import build_messages  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=("zero_shot", "few_shot"), required=True)
    parser.add_argument("--split", choices=("development", "test"), default="development")
    parser.add_argument("--meeting-id", action="append", help="Repeat to run selected meetings only.")
    parser.add_argument("--execute", action="store_true", help="Required to spend API credit.")
    parser.add_argument("--prompt-for-key", action="store_true", help="Read the API key from a hidden terminal prompt when the environment variable is absent.")
    parser.add_argument("--allow-test", action="store_true", help="Second safety switch for formal test execution.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/llm_experiment_v1.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/data_manifest.csv")
    parser.add_argument("--transcript-dir", type=Path, default=ROOT / "data/derived/transcripts")
    parser.add_argument("--metadata-dir", type=Path, default=ROOT / "data/derived/metadata")
    parser.add_argument("--prompt-dir", type=Path, default=ROOT / "prompts")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas/action_output_v1.schema.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/raw_api")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split == "test" and not args.allow_test:
        print("REFUSED: formal test execution requires --allow-test after every freeze gate passes.", file=sys.stderr)
        return 2
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.split == "test" and not config["version"].endswith("-frozen"):
        print("REFUSED: LLM experiment configuration is not frozen.", file=sys.stderr)
        return 2
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["split"] == args.split]
    if args.meeting_id:
        requested = set(args.meeting_id)
        rows = [row for row in rows if row["meeting_id"] in requested]
        missing = requested - {row["meeting_id"] for row in rows}
        if missing:
            raise ValueError(f"Requested meetings are not in {args.split}: {sorted(missing)}")
    plan = [row["meeting_id"] for row in rows]
    print(f"Plan: {args.condition} on {args.split}: {', '.join(plan)}")
    if not args.execute:
        print("DRY PLAN ONLY: add --execute to make API calls.")
        return 0

    key_name = config["api_key_environment_variable"]
    api_key = os.environ.get(key_name)
    if not api_key and args.prompt_for_key:
        api_key = getpass.getpass("OpenRouter API key (hidden): ").strip()
    if not api_key:
        print(f"REFUSED: environment variable {key_name} is not set.", file=sys.stderr)
        return 2
    client = OpenAI(base_url=config["base_url"], api_key=api_key)
    run_dir = args.output_dir / config["version"] / args.condition / args.split
    run_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        meeting_id = row["meeting_id"]
        transcript_path = args.transcript_dir / f"{meeting_id}.txt"
        metadata_path = args.metadata_dir / f"{meeting_id}.json"
        transcript = transcript_path.read_text(encoding="utf-8")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        messages = build_messages(
            condition=args.condition,
            meeting_id=meeting_id,
            meeting_date=metadata.get("date") or "",
            transcript=transcript,
            prompt_dir=args.prompt_dir,
        )
        user_content = messages[-1]["content"]
        submitted = user_content.split("<transcript>\n", 1)[1].rsplit("\n</transcript>", 1)[0]
        coverage_issues = validate_complete_input(transcript, submitted)
        if coverage_issues:
            raise RuntimeError(coverage_issues[0].message)
        result = execute_extraction(
            client=client,
            config=config,
            schema=schema,
            messages=messages,
            metadata=metadata,
        )
        record = {
            "run": {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "condition": args.condition,
                "split": args.split,
                "meeting_id": meeting_id,
                "provider": config["provider"],
                "requested_model": config["model"],
                "temperature": config["temperature"],
                "max_output_tokens": config["max_output_tokens"],
                "config_version": config["version"],
                "config_sha256": sha256(args.config),
                "schema_sha256": sha256(args.schema),
                "prompt_hash": canonical_hash(messages),
                "transcript_sha256": sha256(transcript_path),
                "complete_transcript_submitted": True,
            },
            **result,
        }
        output_path = run_dir / f"{meeting_id}.json"
        output_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{meeting_id}: {result['status']}, retries={result['retry_count']}, cost≈${result['usage_total']['estimated_cost_usd']:.4f}")
        failures += result["status"] != "valid"
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
