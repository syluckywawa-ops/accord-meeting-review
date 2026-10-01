"""Versioned message construction shared by zero-shot and few-shot arms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_prompt_assets(prompt_dir: Path) -> tuple[str, str, list[dict[str, Any]]]:
    system = (prompt_dir / "system_v1.txt").read_text(encoding="utf-8").strip()
    user_template = (prompt_dir / "user_template_v1.txt").read_text(encoding="utf-8").strip()
    examples = json.loads((prompt_dir / "few_shot_examples_v1.json").read_text(encoding="utf-8"))
    return system, user_template, examples


def build_messages(
    *,
    condition: str,
    meeting_id: str,
    meeting_date: str,
    transcript: str,
    prompt_dir: Path,
) -> list[dict[str, str]]:
    if condition not in {"zero_shot", "few_shot"}:
        raise ValueError("condition must be zero_shot or few_shot")
    system, user_template, examples = load_prompt_assets(prompt_dir)
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if condition == "few_shot":
        for example in examples:
            messages.append({"role": "user", "content": example["input"]})
            messages.append(
                {"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)}
            )
    user = user_template.format(
        meeting_id=meeting_id,
        meeting_date=meeting_date or "unknown",
        transcript=transcript,
    )
    messages.append({"role": "user", "content": user})
    return messages

