#!/usr/bin/env python3
"""Validate ActionAI manual labels against the locked manifest and transcript turns."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REQUIRED_COLUMNS = (
    "transcript_id",
    "action_id",
    "task",
    "owner",
    "deadline_text",
    "deadline_normalized",
    "evidence_text",
    "evidence_ids",
    "explicitness",
    "notes",
    "label_status",
    "annotation_started_at",
    "annotation_finished_at",
    "annotation_minutes",
)

ALLOWED_OWNERS = {
    "Project Manager",
    "Marketing Expert",
    "Industrial Designer",
    "User Interface Designer",
    "Team",
}
ALLOWED_EXPLICITNESS = {"explicit", "self_commitment", "implicit_task"}
ALLOWED_STATUS = {"draft", "initial_locked", "adjudicated_gold"}
ACTION_ID_PATTERN = re.compile(r"^(?P<meeting>[A-Z]{2}\d{4}[a-d])-A\d{3}$")


@dataclass(frozen=True)
class Issue:
    severity: str
    location: str
    message: str


def normalise_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row
            for row in reader
            if any(str(value or "").strip() for value in row.values())
        ]
        return list(reader.fieldnames or []), rows


def valid_owner_field(value: str) -> bool:
    cleaned = value.strip()
    if not cleaned:
        return True
    owners = [owner.strip() for owner in cleaned.split(";") if owner.strip()]
    if not owners or any(owner not in ALLOWED_OWNERS for owner in owners):
        return False
    if "Team" in owners and len(owners) > 1:
        return False
    return len(owners) == len(set(owners))


def parse_iso_datetime(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


def valid_iso_deadline(value: str) -> bool:
    cleaned = value.strip().replace("Z", "+00:00")
    if not cleaned:
        return True
    try:
        datetime.fromisoformat(cleaned)
        return True
    except ValueError:
        try:
            datetime.strptime(cleaned, "%Y-%m-%d")
            return True
        except ValueError:
            return False


def load_turns(metadata_dir: Path, meeting_id: str) -> dict[str, str]:
    path = metadata_dir / f"{meeting_id}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {turn["turn_id"]: turn["text"] for turn in payload["turns"]}


def validate(
    labels_path: Path,
    manifest_path: Path,
    metadata_dir: Path,
    require_all_locked: bool = False,
) -> tuple[list[Issue], dict[str, int]]:
    issues: list[Issue] = []
    headers, rows = read_csv(labels_path)
    missing_headers = [column for column in REQUIRED_COLUMNS if column not in headers]
    extra_headers = [column for column in headers if column not in REQUIRED_COLUMNS]
    if missing_headers:
        issues.append(Issue("ERROR", "header", f"Missing columns: {', '.join(missing_headers)}"))
        return issues, {"rows": len(rows), "transcripts": 0, "errors": 1, "warnings": 0}
    if extra_headers:
        issues.append(Issue("WARNING", "header", f"Unexpected columns: {', '.join(extra_headers)}"))

    _, manifest_rows = read_csv(manifest_path)
    manifest = {row["meeting_id"]: row for row in manifest_rows}
    turns_cache: dict[str, dict[str, str]] = {}
    action_ids: set[str] = set()
    labelled_meetings: set[str] = set()
    transcript_session_values: dict[str, tuple[str, str, str]] = {}

    for index, row in enumerate(rows, start=2):
        location = f"row {index}"
        meeting_id = row["transcript_id"].strip()
        action_id = row["action_id"].strip()
        labelled_meetings.add(meeting_id)

        if meeting_id not in manifest:
            issues.append(Issue("ERROR", location, f"Unknown transcript_id {meeting_id!r}"))
            continue

        expected_match = ACTION_ID_PATTERN.fullmatch(action_id)
        if not expected_match or expected_match.group("meeting") != meeting_id:
            issues.append(
                Issue("ERROR", location, f"action_id must look like {meeting_id}-A001 and match transcript_id")
            )
        if action_id in action_ids:
            issues.append(Issue("ERROR", location, f"Duplicate action_id {action_id!r}"))
        action_ids.add(action_id)

        if not row["task"].strip():
            issues.append(Issue("ERROR", location, "task is empty"))
        if not valid_owner_field(row["owner"]):
            issues.append(
                Issue(
                    "ERROR",
                    location,
                    "owner must be blank, Team, or unique normalised AMI roles separated by '; ': "
                    f"{row['owner']!r}",
                )
            )
        if row["explicitness"].strip() not in ALLOWED_EXPLICITNESS:
            issues.append(Issue("ERROR", location, f"Invalid explicitness {row['explicitness']!r}"))
        status = row["label_status"].strip()
        if status not in ALLOWED_STATUS:
            issues.append(Issue("ERROR", location, f"Invalid label_status {status!r}"))
        if row["deadline_normalized"].strip() and not row["deadline_text"].strip():
            issues.append(Issue("ERROR", location, "deadline_normalized exists but deadline_text is empty"))
        if not valid_iso_deadline(row["deadline_normalized"]):
            issues.append(Issue("ERROR", location, f"Invalid ISO deadline {row['deadline_normalized']!r}"))

        if meeting_id not in turns_cache:
            try:
                turns_cache[meeting_id] = load_turns(metadata_dir, meeting_id)
            except (FileNotFoundError, KeyError, json.JSONDecodeError) as error:
                issues.append(Issue("ERROR", location, f"Cannot load transcript metadata: {error}"))
                turns_cache[meeting_id] = {}

        evidence_ids = [item.strip() for item in row["evidence_ids"].split("|") if item.strip()]
        evidence_chunks = [item.strip() for item in row["evidence_text"].split(" || ") if item.strip()]
        if not evidence_ids:
            issues.append(Issue("ERROR", location, "evidence_ids is empty"))
        if not evidence_chunks:
            issues.append(Issue("ERROR", location, "evidence_text is empty"))
        if evidence_ids and evidence_chunks and len(evidence_ids) != len(evidence_chunks):
            issues.append(
                Issue(
                    "ERROR",
                    location,
                    "Multiple evidence spans require one turn ID per quote, using | for IDs and ' || ' for text",
                )
            )
        for evidence_id, evidence_text in zip(evidence_ids, evidence_chunks):
            turn_text = turns_cache[meeting_id].get(evidence_id)
            if turn_text is None:
                issues.append(Issue("ERROR", location, f"Unknown evidence turn {evidence_id!r}"))
            elif normalise_text(evidence_text) not in normalise_text(turn_text):
                issues.append(
                    Issue("ERROR", location, f"evidence_text is not verbatim within {evidence_id}")
                )

        started = row["annotation_started_at"].strip()
        finished = row["annotation_finished_at"].strip()
        minutes = row["annotation_minutes"].strip()
        if status == "initial_locked" and not all((started, finished, minutes)):
            issues.append(Issue("ERROR", location, "Initial locked labels require start, finish, and minutes"))
        if status == "adjudicated_gold" and not all((started, finished, minutes)):
            issues.append(
                Issue(
                    "WARNING",
                    location,
                    "Post-lock gold addition has no original manual-annotation timing; keep this blank rather than inventing a value",
                )
            )
        if started and finished:
            try:
                start_dt = parse_iso_datetime(started)
                finish_dt = parse_iso_datetime(finished)
                if finish_dt < start_dt:
                    issues.append(Issue("ERROR", location, "annotation_finished_at precedes start"))
            except ValueError:
                issues.append(Issue("ERROR", location, "Annotation timestamps must be ISO 8601"))
        if minutes:
            try:
                if float(minutes) <= 0:
                    raise ValueError
            except ValueError:
                issues.append(Issue("ERROR", location, "annotation_minutes must be a positive number"))

        session = (started, finished, minutes)
        prior_session = transcript_session_values.setdefault(meeting_id, session)
        if session != prior_session:
            issues.append(Issue("ERROR", location, "Timing fields disagree within the same transcript"))

    if not rows:
        issues.append(Issue("WARNING", "file", "No action rows have been entered yet"))

    if require_all_locked:
        missing_meetings = sorted(set(manifest) - labelled_meetings)
        if missing_meetings:
            issues.append(
                Issue("ERROR", "coverage", f"No label rows for: {', '.join(missing_meetings)}")
            )
        unlocked = sorted(
            {
                row["transcript_id"]
                for row in rows
                if row["label_status"].strip() not in {"initial_locked", "adjudicated_gold"}
            }
        )
        if unlocked:
            issues.append(Issue("ERROR", "coverage", f"Unlocked transcript labels: {', '.join(unlocked)}"))

    error_count = sum(issue.severity == "ERROR" for issue in issues)
    warning_count = sum(issue.severity == "WARNING" for issue in issues)
    return issues, {
        "rows": len(rows),
        "transcripts": len(labelled_meetings),
        "errors": error_count,
        "warnings": warning_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--require-all-locked", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues, summary = validate(
        args.labels, args.manifest, args.metadata_dir, args.require_all_locked
    )
    for issue in issues:
        print(f"{issue.severity}: {issue.location}: {issue.message}")
    print(
        "Validated {rows} rows across {transcripts} transcripts: "
        "{errors} errors, {warnings} warnings.".format(**summary)
    )
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
