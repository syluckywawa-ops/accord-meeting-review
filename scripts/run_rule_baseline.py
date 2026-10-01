#!/usr/bin/env python3
"""Run the deterministic ActionAI rule baseline on a manifest split."""

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

from actionai.rule_baseline import extract_actions, load_config  # noqa: E402


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "test"), default="development")
    parser.add_argument("--allow-test", action="store_true", help="Required safety switch for locked test data.")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/data_manifest.csv")
    parser.add_argument("--metadata-dir", type=Path, default=ROOT / "data/derived/metadata")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/rule_baseline_v1.json")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split == "test" and not args.allow_test:
        print("REFUSED: test execution requires --allow-test after the formal freeze gate.", file=sys.stderr)
        return 2

    config, config_hash = load_config(args.config)
    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        meetings = [row for row in csv.DictReader(handle) if row["split"] == args.split]

    output_path = args.output or ROOT / f"outputs/rule-baseline/{config['version']}/{args.split}.json"
    results = []
    for row in meetings:
        path = args.metadata_dir / f"{row['meeting_id']}.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("split") != args.split:
            raise ValueError(f"Split mismatch for {row['meeting_id']}")
        results.append(
            {
                "transcript_id": row["meeting_id"],
                "transcript_sha256": file_sha256(path),
                "action_items": extract_actions(metadata, config),
            }
        )

    payload = {
        "run": {
            "system": "keyword-rule baseline",
            "version": config["version"],
            "split": args.split,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "config_sha256": config_hash,
            "meeting_count": len(results),
            "randomness": "none",
            "network_calls": 0,
        },
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    count = sum(len(result["action_items"]) for result in results)
    print(f"Wrote {count} predictions for {len(results)} {args.split} meetings to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

