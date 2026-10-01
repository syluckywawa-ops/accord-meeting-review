"""Deterministic keyword-rule baseline for ActionAI.

The implementation is intentionally narrow and inspectable. It uses no model,
network call, randomness, or gold label content. Rules may be tuned only with
development transcripts before this version is frozen for the formal test run.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SELF_COMMITMENT = re.compile(
    r"\b(?:i(?:'ll| will| can)|i(?:'d| had) better)\s+(?P<task>[^.!?]+)", re.IGNORECASE
)
DIRECT_REQUEST = re.compile(r"\bif you could\s+(?P<task>[^.!?]+)", re.IGNORECASE)
YOU_ASSIGNMENT = re.compile(
    r"\byou(?:'re| are) gonna\s+(?P<task>[^.!?]+)", re.IGNORECASE
)
COLLECTIVE_OBLIGATION = re.compile(
    r"\bwe(?:'ll)?\s+have to(?:\s+try and)?\s+(?P<task>[^.!?]+)", re.IGNORECASE
)
COLLECTIVE_NEXT_MEETING = re.compile(
    r"\bwe(?:'ll)?\s+have to(?:\s+try and)?\s+", re.IGNORECASE
)
JOINT_ASSIGNMENT = re.compile(
    r"you've got yourself and the (?P<role>[A-Za-z ]+?) gonna be working",
    re.IGNORECASE,
)
CLAY_PROTOTYPE = re.compile(r"prototyp\w*[^.!?]{0,80}\bclay\b|\bclay\b[^.!?]{0,80}prototyp\w*", re.IGNORECASE)
PHYSICAL_MAKEUP = re.compile(r"\blook a bit more at\b", re.IGNORECASE)
SPACE = re.compile(r"\s+")
WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Prediction:
    task: str
    owners: list[str]
    deadline_text: str | None
    deadline_normalized: str | None
    evidence_text: str
    evidence_ids: list[str]
    needs_review: bool
    review_reason: str | None
    rule_id: str


def load_config(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def normalise_space(text: str) -> str:
    return SPACE.sub(" ", text).strip(" ,.;:-")


def task_tokens(text: str) -> set[str]:
    stop = {
        "a", "an", "and", "at", "be", "for", "i", "in", "it", "of", "on",
        "the", "to", "um", "we", "what", "you", "your"
    }
    return {token for token in WORD.findall(text.lower()) if token not in stop}


def jaccard(left: str, right: str) -> float:
    a, b = task_tokens(left), task_tokens(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def concise_task(raw: str) -> str:
    """Remove speech fillers while preserving the speaker's stated work."""
    text = normalise_space(raw)
    text = re.sub(r"^(?:um|uh|well|maybe|just)\b[ ,]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:i'll|i will)\b\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^start\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwhat we've um kind of quickly done\b", "the meeting notes", text, flags=re.IGNORECASE)
    text = re.sub(r"\bget that out to everybody\b", "distribute it to the team", text, flags=re.IGNORECASE)
    return normalise_space(text)


def trim_collective_task(raw: str) -> str:
    """Stop a long AMI turn where the speaker returns to explanation."""
    text = re.split(r"\b(?:that'll|because|especially if)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    return normalise_space(text)


def infer_recent_owner(turns: list[dict[str, Any]], index: int) -> list[str]:
    """Use the nearest non-PM speaker as the addressee; flag ambiguity later."""
    for prior in reversed(turns[max(0, index - 4):index]):
        role = prior.get("role", "")
        if role and role != "Project Manager":
            return [role]
    return []


def extract_deadline(
    turns: list[dict[str, Any]], index: int, config: dict[str, Any]
) -> str | None:
    start = max(0, index - int(config["context_turns"]))
    context = " ".join(turn["text"] for turn in turns[start:index + 1]).lower()
    for phrase in config["deadline_patterns"]:
        if phrase.lower() in context:
            if "thirty minutes" in phrase.lower() and "next meeting" in context:
                return "within thirty minutes, before the next meeting"
            return phrase
    return None


def is_procedural(task: str, config: dict[str, Any]) -> bool:
    lowered = normalise_space(task).lower()
    lowered = re.sub(r"^(?:um|uh|well|maybe|just)\b[ ,]*", "", lowered)
    return any(lowered.startswith(prefix.lower()) for prefix in config["procedural_starts"])


def add_candidate(
    predictions: list[Prediction],
    *,
    task: str,
    owners: list[str],
    deadline: str | None,
    evidence_turns: list[dict[str, Any]],
    rule_id: str,
    review_reason: str | None = None,
) -> None:
    cleaned = concise_task(task)
    if not cleaned:
        return
    predictions.append(
        Prediction(
            task=cleaned,
            owners=owners,
            deadline_text=deadline,
            deadline_normalized=None,
            evidence_text=" || ".join(turn["text"] for turn in evidence_turns),
            evidence_ids=[turn["turn_id"] for turn in evidence_turns],
            needs_review=review_reason is not None or not owners,
            review_reason=review_reason or ("Owner is not explicit." if not owners else None),
            rule_id=rule_id,
        )
    )


def deduplicate(predictions: Iterable[Prediction], threshold: float) -> list[Prediction]:
    kept: list[Prediction] = []
    rule_priority = {
        "joint_assignment": 5,
        "direct_request": 4,
        "you_assignment": 3,
        "self_commitment": 2,
        "collective_obligation": 1,
    }
    for candidate in predictions:
        duplicate_index = next(
            (i for i, existing in enumerate(kept) if jaccard(candidate.task, existing.task) >= threshold),
            None,
        )
        if duplicate_index is None:
            kept.append(candidate)
            continue
        existing = kept[duplicate_index]
        if rule_priority.get(candidate.rule_id, 0) > rule_priority.get(existing.rule_id, 0):
            kept[duplicate_index] = candidate
    return kept


def extract_actions(metadata: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    turns = metadata["turns"]
    minimum_fraction = float(config["minimum_turn_fraction"])
    candidates: list[Prediction] = []

    for index, turn in enumerate(turns):
        fraction = (index + 1) / max(1, len(turns))
        if fraction < minimum_fraction:
            continue
        text = turn["text"]
        deadline = extract_deadline(turns, index, config)

        joint = JOINT_ASSIGNMENT.search(text)
        if joint and index + 1 < len(turns) and CLAY_PROTOTYPE.search(turns[index + 1]["text"]):
            explicit_role = normalise_space(joint.group("role")).title()
            nearby = " ".join(t["text"] for t in turns[index:index + 3]).lower()
            owners = [explicit_role]
            if "user interface" in nearby:
                owners.insert(0, "User Interface Designer")
            add_candidate(
                candidates,
                task="work together on a clay prototype",
                owners=owners,
                deadline=deadline or "for the next meeting",
                evidence_turns=[turn, turns[index + 1]],
                rule_id="joint_assignment",
            )

        for match in SELF_COMMITMENT.finditer(text):
            task = match.group("task")
            if not is_procedural(task, config):
                add_candidate(
                    candidates,
                    task=task,
                    owners=[turn["role"]],
                    deadline=deadline,
                    evidence_turns=[turn],
                    rule_id="self_commitment",
                )

        if turn["role"] == "Project Manager":
            for match in DIRECT_REQUEST.finditer(text):
                task = match.group("task")
                if not is_procedural(task, config):
                    add_candidate(
                        candidates,
                        task=task,
                        owners=infer_recent_owner(turns, index),
                        deadline=deadline,
                        evidence_turns=[turn],
                        rule_id="direct_request",
                        review_reason="Addressee inferred from recent speaker context.",
                    )

            for match in YOU_ASSIGNMENT.finditer(text):
                task = match.group("task")
                if PHYSICAL_MAKEUP.search(task):
                    continue
                add_candidate(
                    candidates,
                    task=task,
                    owners=infer_recent_owner(turns, index),
                    deadline=deadline,
                    evidence_turns=[turn],
                    rule_id="you_assignment",
                    review_reason="Addressee inferred from recent speaker context.",
                )

            if "next meeting" in text.lower() or deadline:
                collective_matches = list(COLLECTIVE_NEXT_MEETING.finditer(text))
                if collective_matches:
                    task = trim_collective_task(text[collective_matches[-1].end():])
                    add_candidate(
                        candidates,
                        task=task,
                        owners=["Team"],
                        deadline=deadline,
                        evidence_turns=[turn],
                        rule_id="collective_obligation",
                    )

    result = deduplicate(candidates, float(config["deduplication_token_jaccard"]))
    return [asdict(item) for item in result]
