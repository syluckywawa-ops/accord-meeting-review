"""Dependency-free validation of ActionAI structured outputs and evidence."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any


ALLOWED_OWNERS = {
    "Project Manager",
    "Marketing Expert",
    "Industrial Designer",
    "User Interface Designer",
    "Team",
}
REQUIRED_ITEM_FIELDS = {
    "task",
    "owners",
    "deadline_text",
    "deadline_normalized",
    "evidence_text",
    "evidence_ids",
    "needs_review",
    "review_reason",
}
OPTIONAL_ITEM_FIELDS = {"rule_id"}
TURN_ID = re.compile(r"^[A-Z]{2}\d{4}[a-d]-T\d{4}$")


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str


def normalise_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_complete_input(full_transcript: str, submitted_transcript: str) -> list[ValidationIssue]:
    if sha256_text(full_transcript) == sha256_text(submitted_transcript):
        return []
    return [ValidationIssue("input", "Submitted transcript differs from the complete source; silent truncation is prohibited")]


def valid_iso(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_output(payload: Any, metadata: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(payload, dict):
        return [ValidationIssue("root", "Output must be a JSON object")]
    if set(payload) != {"action_items"}:
        issues.append(ValidationIssue("root", "The only top-level field must be action_items"))
    items = payload.get("action_items")
    if not isinstance(items, list):
        issues.append(ValidationIssue("action_items", "action_items must be an array"))
        return issues

    turns = {turn["turn_id"]: turn["text"] for turn in metadata.get("turns", [])}
    meeting_id = metadata.get("meeting_id", "")
    for index, item in enumerate(items):
        location = f"action_items[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(location, "Action item must be an object"))
            continue
        missing = REQUIRED_ITEM_FIELDS - set(item)
        extra = set(item) - REQUIRED_ITEM_FIELDS - OPTIONAL_ITEM_FIELDS
        if missing:
            issues.append(ValidationIssue(location, f"Missing fields: {', '.join(sorted(missing))}"))
        if extra:
            issues.append(ValidationIssue(location, f"Unexpected fields: {', '.join(sorted(extra))}"))

        task = item.get("task")
        if not isinstance(task, str) or not task.strip():
            issues.append(ValidationIssue(f"{location}.task", "task must be a non-empty string"))

        owners = item.get("owners")
        if not isinstance(owners, list) or any(not isinstance(owner, str) for owner in owners):
            issues.append(ValidationIssue(f"{location}.owners", "owners must be an array of strings"))
        else:
            if len(owners) != len(set(owners)):
                issues.append(ValidationIssue(f"{location}.owners", "owners must be unique"))
            invalid = [owner for owner in owners if owner not in ALLOWED_OWNERS]
            if invalid:
                issues.append(ValidationIssue(f"{location}.owners", f"Unsupported owners: {invalid}"))
            if "Team" in owners and len(owners) > 1:
                issues.append(ValidationIssue(f"{location}.owners", "Team cannot be combined with individual roles"))

        for field in ("deadline_text", "deadline_normalized", "review_reason"):
            if item.get(field) is not None and not isinstance(item.get(field), str):
                issues.append(ValidationIssue(f"{location}.{field}", f"{field} must be a string or null"))
        deadline_normalized = item.get("deadline_normalized")
        if isinstance(deadline_normalized, str) and deadline_normalized and not valid_iso(deadline_normalized):
            issues.append(ValidationIssue(f"{location}.deadline_normalized", "deadline_normalized must be ISO 8601"))
        if deadline_normalized and not item.get("deadline_text"):
            issues.append(ValidationIssue(f"{location}.deadline_normalized", "A normalized deadline requires deadline_text"))

        needs_review = item.get("needs_review")
        if not isinstance(needs_review, bool):
            issues.append(ValidationIssue(f"{location}.needs_review", "needs_review must be boolean"))
        if needs_review is True and not str(item.get("review_reason") or "").strip():
            issues.append(ValidationIssue(f"{location}.review_reason", "A flagged item requires a review reason"))
        if needs_review is False and item.get("review_reason") is not None:
            issues.append(ValidationIssue(f"{location}.review_reason", "Unflagged items must use null review_reason"))
        if isinstance(owners, list) and not owners and needs_review is not True:
            issues.append(ValidationIssue(f"{location}.needs_review", "Missing owner must be flagged for review"))

        evidence_text = item.get("evidence_text")
        evidence_ids = item.get("evidence_ids")
        if not isinstance(evidence_text, str) or not evidence_text.strip():
            issues.append(ValidationIssue(f"{location}.evidence_text", "evidence_text must be a non-empty string"))
        if not isinstance(evidence_ids, list) or not evidence_ids or any(not isinstance(value, str) for value in evidence_ids):
            issues.append(ValidationIssue(f"{location}.evidence_ids", "evidence_ids must be a non-empty string array"))
            continue
        if len(evidence_ids) != len(set(evidence_ids)):
            issues.append(ValidationIssue(f"{location}.evidence_ids", "evidence_ids must be unique"))
        evidence_chunks = [chunk.strip() for chunk in str(evidence_text or "").split(" || ") if chunk.strip()]
        if len(evidence_chunks) != len(evidence_ids):
            issues.append(ValidationIssue(location, "Use one evidence_text chunk per evidence ID, separated by ' || '"))
        for evidence_id, evidence_chunk in zip(evidence_ids, evidence_chunks):
            if not TURN_ID.fullmatch(evidence_id) or not evidence_id.startswith(f"{meeting_id}-T"):
                issues.append(ValidationIssue(f"{location}.evidence_ids", f"Invalid evidence ID {evidence_id!r}"))
                continue
            source = turns.get(evidence_id)
            if source is None:
                issues.append(ValidationIssue(f"{location}.evidence_ids", f"Unknown evidence ID {evidence_id!r}"))
            elif normalise_text(evidence_chunk) not in normalise_text(source):
                issues.append(ValidationIssue(f"{location}.evidence_text", f"Evidence is not verbatim within {evidence_id}"))
    return issues


def parse_and_validate(raw_json: str, metadata: dict[str, Any]) -> tuple[Any | None, list[ValidationIssue]]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as error:
        return None, [ValidationIssue("json", f"Invalid JSON: {error.msg}")]
    return payload, validate_output(payload, metadata)

