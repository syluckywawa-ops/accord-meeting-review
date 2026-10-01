"""Human review sessions, durable audit history and approval-gated exports."""
from __future__ import annotations

import copy
import csv
import io
import re
from datetime import datetime, timezone

from actionai.imported_meetings import validate_review as validate_output


def now():
    return datetime.now(timezone.utc).isoformat()


def new_session(meeting, condition, result):
    valid = result.get("run_status") == "valid"
    return {
        "version": 1, "meeting_id": meeting, "condition": condition,
        "source_status": result.get("run_status"), "created_at": now(),
        "revision": 0, "omissions_checked": False, "history": [],
        "items": [{"id": f"candidate-{i+1}", "origin": "model",
                   "original": copy.deepcopy(item), "current": copy.deepcopy(item),
                   "decision": "pending", "completed": False, "completed_at": None}
                  for i, item in enumerate(result.get("action_items", []) if valid else [])],
    }


def review_hints(session):
    """Advisory product-only triage; never changes candidates or experimental scores."""
    hints = {row["id"]: [] for row in session["items"]}
    model_rows = [row for row in session["items"] if row["origin"] == "model" and row["decision"] != "rejected"]

    def task_terms(row):
        words = re.findall(r"[\w]+", str(row["current"].get("task", "")).casefold())
        return {word for word in words if word not in {"a", "an", "and", "for", "of", "the", "to"}}

    for index, left in enumerate(model_rows):
        left_terms = task_terms(left)
        for right in model_rows[index + 1:]:
            right_terms = task_terms(right)
            overlap = len(left_terms & right_terms)
            if not left_terms or not right_terms or overlap < 3:
                continue
            similar = overlap / len(left_terms | right_terms) >= 0.75
            fragment = left_terms <= right_terms or right_terms <= left_terms
            if similar or fragment:
                for row, other in ((left, right), (right, left)):
                    hints[row["id"]].append({"code": "possible_duplicate", "message":
                                             f"Possibly overlaps {other['id']}; compare both tasks before approving."})

    for row in model_rows:
        item = row["current"]
        quote = str(item.get("evidence_text") or "")
        words = re.findall(r"[\w]+", quote.casefold())
        if len(words) < 6 or (len(words) < 16 and any(w in {"that", "this", "it", "those"} for w in words)):
            hints[row["id"]].append({"code": "thin_evidence", "message":
                                     "Quote may need surrounding turns for context; inspect the source before approving."})
    return hints


def apply_review(session, operation, metadata):
    """Return a new state; reject bad edits before mutating saved state."""
    updated = copy.deepcopy(session)
    action = operation.get("action")
    event = {"at": now(), "action": action}
    if action == "confirm_scan":
        updated["omissions_checked"] = bool(operation.get("value"))
    elif action == "add":
        item = copy.deepcopy(operation["item"])
        issues = validate_output({"action_items": [item]}, metadata)
        if issues:
            raise ValueError("; ".join(x.message for x in issues))
        item_id = f"manual-{updated['revision'] + 1}"
        updated["items"].append({"id": item_id, "origin": "human", "original": None,
                                 "current": item, "decision": "accepted", "completed": False,
                                 "completed_at": None})
        event.update({"item_id": item_id, "after": item})
        updated["omissions_checked"] = False
    elif action == "set_completed":
        row = next((x for x in updated["items"] if x["id"] == operation.get("id")), None)
        if row is None or row["decision"] not in {"accepted", "edited"}:
            raise ValueError("Only approved actions can be marked complete")
        value = operation.get("value")
        if not isinstance(value, bool):
            raise ValueError("Completion must be true or false")
        event.update({"item_id": row["id"], "before": copy.deepcopy(row)})
        row["completed"] = value
        row["completed_at"] = (row.get("completed_at") or event["at"]) if value else None
        event["after"] = copy.deepcopy(row)
    elif action in {"accept", "edit", "reject", "reopen"}:
        row = next((x for x in updated["items"] if x["id"] == operation.get("id")), None)
        if row is None:
            raise ValueError("Unknown action item")
        event.update({"item_id": row["id"], "before": copy.deepcopy(row)})
        if action == "edit":
            row["current"] = copy.deepcopy(operation["item"])
        if action in {"accept", "edit"}:
            issues = validate_output({"action_items": [row["current"]]}, metadata)
            if issues:
                raise ValueError("; ".join(x.message for x in issues))
        row["decision"] = {"accept": "accepted", "edit": "edited", "reject": "rejected",
                           "reopen": "pending"}[action]
        row["completed"] = False
        row["completed_at"] = None
        event["after"] = copy.deepcopy(row)
        updated["omissions_checked"] = False
    else:
        raise ValueError("Unknown review operation")
    updated["revision"] += 1
    updated["history"].append(event)
    return updated


def approved_items(session, metadata):
    if any(x["decision"] == "pending" for x in session["items"]):
        raise ValueError("Review every candidate before export")
    if not session["omissions_checked"]:
        raise ValueError("Check the full transcript for missed actions before export")
    items = [copy.deepcopy(x["current"]) for x in session["items"]
             if x["decision"] in {"accepted", "edited"}]
    issues = validate_output({"action_items": items}, metadata)
    if issues:
        raise ValueError("; ".join(x.message for x in issues))
    return items


def task_tracking(session):
    """Operational completion metadata, separate from the frozen extraction schema."""
    return [{"id": row["id"], "completed": bool(row.get("completed", False)),
             "completed_at": row.get("completed_at")}
            for row in session["items"] if row["decision"] in {"accepted", "edited"}]


def export_csv(items, tracking=None):
    stream = io.StringIO()
    fields = ["task", "owners", "deadline_text", "deadline_normalized", "evidence_text", "evidence_ids",
              "needs_review", "review_reason"]
    if tracking is not None:
        if len(tracking) != len(items):
            raise ValueError("Tracking must correspond to approved items")
        fields += ["completed", "completed_at"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for index, item in enumerate(items):
        row = {key: item.get(key) for key in fields}
        if tracking is not None:
            row.update({key: tracking[index][key] for key in ("completed", "completed_at")})
        for key in ("owners", "evidence_ids"):
            row[key] = "; ".join(row[key])
        # Spreadsheet formula injection prevention for human-entered text.
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                row[key] = "'" + value
        writer.writerow(row)
    return "\ufeff" + stream.getvalue()
