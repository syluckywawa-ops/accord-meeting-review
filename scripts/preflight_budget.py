#!/usr/bin/env python3
"""Count model-specific prompt tokens and calculate a conservative experiment budget."""

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

import tiktoken  # noqa: E402

from actionai.prompts import build_messages  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_messages(messages: list[dict[str, str]], schema: dict, encoding) -> int:
    # Conservative local preflight: encoded content plus role/framing allowance.
    content_tokens = sum(len(encoding.encode(message["content"])) for message in messages)
    framing_tokens = 4 * len(messages) + 3
    schema_tokens = len(encoding.encode(json.dumps(schema, separators=(",", ":"))))
    return content_tokens + framing_tokens + schema_tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/llm_experiment_v1.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/data_manifest.csv")
    parser.add_argument("--transcript-dir", type=Path, default=ROOT / "data/derived/transcripts")
    parser.add_argument("--metadata-dir", type=Path, default=ROOT / "data/derived/metadata")
    parser.add_argument("--prompt-dir", type=Path, default=ROOT / "prompts")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas/action_output_v1.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/preflight/token_budget_v1.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    encoding = tiktoken.get_encoding(config["tokenizer"])
    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        manifest = list(csv.DictReader(handle))

    records = []
    for row in manifest:
        meeting_id = row["meeting_id"]
        transcript_path = args.transcript_dir / f"{meeting_id}.txt"
        metadata_path = args.metadata_dir / f"{meeting_id}.json"
        transcript = transcript_path.read_text(encoding="utf-8")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for condition in ("zero_shot", "few_shot"):
            messages = build_messages(
                condition=condition,
                meeting_id=meeting_id,
                meeting_date=metadata.get("date") or "",
                transcript=transcript,
                prompt_dir=args.prompt_dir,
            )
            input_tokens = count_messages(messages, schema, encoding)
            if input_tokens + config["max_output_tokens"] > config["context_window_tokens"]:
                coverage = "not_processable"
            else:
                coverage = "processable"
            records.append(
                {
                    "meeting_id": meeting_id,
                    "split": row["split"],
                    "condition": condition,
                    "estimated_input_tokens": input_tokens,
                    "reserved_output_tokens": config["max_output_tokens"],
                    "context_utilization": (input_tokens + config["max_output_tokens"]) / config["context_window_tokens"],
                    "coverage": coverage,
                    "transcript_sha256": sha256(transcript_path),
                }
            )

    input_total = sum(item["estimated_input_tokens"] for item in records)
    output_reserved = sum(item["reserved_output_tokens"] for item in records)
    input_cost = input_total / 1_000_000 * config["input_usd_per_million_tokens"]
    output_cost = output_reserved / 1_000_000 * config["output_usd_per_million_tokens"]
    payload = {
        "preflight": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "config_version": config["version"],
            "model": config["model"],
            "tokenizer": config["tokenizer"],
            "method": "local model-tokenizer estimate including messages and compact JSON schema",
            "actual_api_usage_required_after_run": True,
            "config_sha256": sha256(args.config),
            "schema_sha256": sha256(args.schema),
        },
        "summary": {
            "calls": len(records),
            "estimated_input_tokens": input_total,
            "reserved_output_tokens": output_reserved,
            "estimated_input_cost_usd": input_cost,
            "worst_case_output_cost_usd": output_cost,
            "worst_case_total_cost_usd": input_cost + output_cost,
            "budget_usd": 10.0,
            "within_budget": input_cost + output_cost <= 10.0,
            "not_processable": sum(item["coverage"] != "processable" for item in records),
        },
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {args.output}")
    return 0 if payload["summary"]["within_budget"] and not payload["summary"]["not_processable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
