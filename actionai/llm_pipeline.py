"""One-call structured LLM extraction with one schema-repair retry at most."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict
from typing import Any

from actionai.output_validation import parse_and_validate


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def response_format(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {"name": "actionai_output", "strict": True, "schema": schema},
    }


def evidence_repair_context(
    payload: Any, issues: list[Any], metadata: dict[str, Any]
) -> str:
    """Return exact source turns for items whose evidence failed validation."""
    if not isinstance(payload, dict) or not isinstance(payload.get("action_items"), list):
        return ""
    affected_indices: set[int] = set()
    for issue in issues:
        match = re.match(r"action_items\[(\d+)\]", issue.location)
        if match and ("evidence" in issue.location or "evidence" in issue.message):
            affected_indices.add(int(match.group(1)))
    if not affected_indices:
        return ""
    turns = {turn["turn_id"]: turn["text"] for turn in metadata.get("turns", [])}
    cited_ids = []
    for index in sorted(affected_indices):
        items = payload["action_items"]
        if index >= len(items) or not isinstance(items[index], dict):
            continue
        for evidence_id in items[index].get("evidence_ids", []):
            if evidence_id in turns and evidence_id not in cited_ids:
                cited_ids.append(evidence_id)
    if not cited_ids:
        return ""
    lines = ["Exact cited source turns for evidence repair:"]
    lines.extend(f"{evidence_id}: {turns[evidence_id]}" for evidence_id in cited_ids)
    lines.append(
        "For each retained evidence ID, copy either the complete source text after the ID above or one exact contiguous substring. "
        "Use ' || ' between chunks in the same order as evidence_ids. Remove any unnecessary evidence ID."
    )
    return "\n".join(lines)


def extract_usage(completion: Any, config: dict[str, Any]) -> dict[str, Any]:
    usage = getattr(completion, "usage", None)
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": int(getattr(usage, "total_tokens", input_tokens + output_tokens) or 0),
        "estimated_input_cost_usd": input_tokens / 1_000_000 * config["input_usd_per_million_tokens"],
        "estimated_output_cost_usd": output_tokens / 1_000_000 * config["output_usd_per_million_tokens"],
    }


def execute_extraction(
    *,
    client: Any,
    config: dict[str, Any],
    schema: dict[str, Any],
    messages: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    attempts = []
    working_messages = list(messages)
    max_attempts = 1 + int(config["maximum_schema_repair_retries"])
    final_payload = None
    final_issues = []

    for attempt_index in range(max_attempts):
        started = time.perf_counter()
        completion = client.chat.completions.create(
            model=config["model"],
            messages=working_messages,
            temperature=config["temperature"],
            max_tokens=config["max_output_tokens"],
            response_format=response_format(schema),
            extra_body={"provider": {"require_parameters": config["provider_require_parameters"]}},
        )
        latency = time.perf_counter() - started
        content = completion.choices[0].message.content or ""
        payload, issues = parse_and_validate(content, metadata)
        usage = extract_usage(completion, config)
        attempts.append(
            {
                "attempt": attempt_index + 1,
                "response_id": getattr(completion, "id", None),
                "resolved_model": getattr(completion, "model", None),
                "latency_seconds": latency,
                "raw_content": content,
                "valid": not issues,
                "validation_issues": [asdict(issue) for issue in issues],
                "usage": usage,
            }
        )
        final_payload, final_issues = payload, issues
        if not issues:
            break
        if attempt_index + 1 < max_attempts:
            repair_summary = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
            source_context = evidence_repair_context(payload, issues, metadata)
            working_messages.extend(
                [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "Repair only the JSON/schema/evidence-format errors listed below. "
                            "Do not add new action items or reinterpret the transcript. "
                            "For evidence errors, evidence_text must be an exact copied substring from each cited turn, "
                            "with no wrapping quotation marks, no parenthesized turn ID, no speaker label, no ellipsis, "
                            "and no corrected or omitted filler words. Return the full corrected JSON object.\n"
                            + repair_summary
                            + ("\n\n" + source_context if source_context else "")
                        ),
                    },
                ]
            )

    total_input = sum(attempt["usage"]["input_tokens"] for attempt in attempts)
    total_output = sum(attempt["usage"]["output_tokens"] for attempt in attempts)
    total_cost = sum(
        attempt["usage"]["estimated_input_cost_usd"] + attempt["usage"]["estimated_output_cost_usd"]
        for attempt in attempts
    )
    return {
        "status": "valid" if not final_issues else "invalid",
        "parsed_output": final_payload,
        "retry_count": len(attempts) - 1,
        "attempts": attempts,
        "usage_total": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "estimated_cost_usd": total_cost,
        },
    }
