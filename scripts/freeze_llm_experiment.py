#!/usr/bin/env python3
"""Freeze the reviewed LLM experiment configuration before any test call."""

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
    parser.add_argument("--dev-config", type=Path, default=ROOT / "configs/llm_experiment_v1.json")
    parser.add_argument("--frozen-config", type=Path, default=ROOT / "configs/llm_experiment_v1_frozen.json")
    parser.add_argument("--output", type=Path, default=ROOT / "configs/LLM_EXPERIMENT_VERSION.json")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    dev_config = read_json(args.dev_config)
    if not dev_config["version"].endswith("-dev"):
        raise ValueError("Source LLM configuration must be a development version")

    evidence = {
        "zero_shot": {
            "predictions": ROOT / "outputs/llm-evaluation/zero-shot-v1.0-dev/development.json",
            "review": ROOT / "outputs/llm-evaluation/zero-shot-v1.0-dev/development_match_review.csv",
            "metrics": ROOT / "outputs/llm-evaluation/zero-shot-v1.0-dev/development_metrics.json",
        },
        "few_shot": {
            "predictions": ROOT / "outputs/llm-evaluation/few-shot-v1.0-dev/development.json",
            "review": ROOT / "outputs/llm-evaluation/few-shot-v1.0-dev/development_match_review.csv",
            "metrics": ROOT / "outputs/llm-evaluation/few-shot-v1.0-dev/development_metrics.json",
        },
    }
    summaries = {}
    for condition, paths in evidence.items():
        for path in paths.values():
            if not path.exists():
                raise FileNotFoundError(path)
        predictions = read_json(paths["predictions"])
        metrics = read_json(paths["metrics"])
        if predictions["run"]["split"] != "development":
            raise ValueError(f"{condition} predictions are not development-only")
        if predictions["run"]["version"] != dev_config["version"]:
            raise ValueError(f"{condition} prediction version differs from the source config")
        if metrics["evaluation"]["split"] != "development":
            raise ValueError(f"{condition} metrics are not development-only")
        summaries[condition] = metrics["task_detection"]

    frozen_config = {**dev_config, "version": dev_config["version"].removesuffix("-dev") + "-frozen"}
    args.frozen_config.parent.mkdir(parents=True, exist_ok=True)
    args.frozen_config.write_text(json.dumps(frozen_config, indent=2) + "\n", encoding="utf-8")

    files = {
        "development_config": args.dev_config,
        "frozen_config": args.frozen_config,
        "schema": ROOT / "schemas/action_output_v1.schema.json",
        "system_prompt": ROOT / "prompts/system_v1.txt",
        "user_prompt": ROOT / "prompts/user_template_v1.txt",
        "few_shot_examples": ROOT / "prompts/few_shot_examples_v1.json",
        "prompt_builder": ROOT / "actionai/prompts.py",
        "llm_pipeline": ROOT / "actionai/llm_pipeline.py",
        "output_validation": ROOT / "actionai/output_validation.py",
        "evaluation": ROOT / "actionai/evaluation.py",
        "runner": ROOT / "scripts/run_llm_experiment.py",
        "collector": ROOT / "scripts/collect_llm_outputs.py",
        "review_finalizer": ROOT / "scripts/finalize_match_review.py",
        "locked_gold_labels": ROOT / "data/labels/final_gold_labels.csv",
        "gold_version": ROOT / "data/labels/LABEL_VERSION.json",
        "data_manifest": ROOT / "data/data_manifest.csv",
        "manual_review_sample": ROOT / "configs/MANUAL_REVIEW_SAMPLE.json",
        "protocol": ROOT / "EXPERIMENT_PROTOCOL_v1.md",
        "protocol_amendment": ROOT / "docs/PROTOCOL_AMENDMENT_v1_1.md",
    }
    for condition, paths in evidence.items():
        for kind, path in paths.items():
            files[f"{condition}_development_{kind}"] = path
    for path in files.values():
        if not path.exists():
            raise FileNotFoundError(path)

    payload = {
        "version": frozen_config["version"],
        "status": "frozen_before_test",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "development_meetings": ["ES2003a", "ES2003b", "ES2003c"],
        "formal_test_meeting_count": 20,
        "formal_conditions": ["zero_shot", "few_shot"],
        "test_outputs_seen": False,
        "change_policy": "Any post-freeze change requires a new version and complete rerun of every affected formal arm.",
        "development_diagnostics": summaries,
        "files": {
            name: {"path": str(path.resolve().relative_to(ROOT)), "sha256": sha256(path.resolve())}
            for name, path in files.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {frozen_config['version']} before test execution")
    print(f"Wrote {args.frozen_config} and {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
