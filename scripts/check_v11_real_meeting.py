#!/usr/bin/env python3
"""Replay an explicitly AI-reviewed, out-of-sample Accord v1.1 check.

This is a product workflow audit, not a new experiment arm or independent human
annotation. The subjective decisions are documented separately in
docs/PRODUCT_V1_1_REAL_MEETING_CHECK.md.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from actionai.imported_meetings import extract_rules
from actionai.review_workspace import apply_review, approved_items, new_session, review_hints


METADATA = ROOT / "data/exploratory_v11/metadata/ES2002a.json"


def main():
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["meeting_id"] == "ES2002a" and len(metadata["turns"]) == 207
    turns = {turn["turn_id"]: turn["text"] for turn in metadata["turns"]}
    session = new_session("ES2002a", "local_rules", extract_rules(metadata))
    assert len(session["items"]) == 3
    initial_hints = review_hints(session)

    for row in session["items"]:
        session = apply_review(session, {"action": "reject", "id": row["id"]}, metadata)

    def add(task, owner, evidence_ids):
        nonlocal session
        item = {
            "task": task,
            "owners": [owner],
            "deadline_text": "before the next meeting in thirty minutes",
            "deadline_normalized": None,
            "evidence_text": " || ".join(turns[turn_id] for turn_id in evidence_ids),
            "evidence_ids": evidence_ids,
            "needs_review": False,
            "review_reason": None,
        }
        session = apply_review(session, {"action": "add", "item": item}, metadata)

    add("develop the working design of the remote control", "Industrial Designer", ["ES2002a-T0176"])
    add("work out the remote control's technical functions", "User Interface Designer", ["ES2002a-T0176"])
    add("identify the remote control's requirements", "Marketing Expert", ["ES2002a-T0176", "ES2002a-T0178"])
    session = apply_review(session, {"action": "confirm_scan", "value": True}, metadata)
    final = approved_items(session, metadata)
    assert len(final) == 3
    print(json.dumps({
        "meeting_id": metadata["meeting_id"],
        "turns_reviewed": len(metadata["turns"]),
        "rule_drafts": 3,
        "rule_drafts_rejected": 3,
        "drafts_flagged_for_thin_evidence": sum(any(h["code"] == "thin_evidence" for h in rows)
                                                for rows in initial_hints.values()),
        "human_added_actions": len(final),
        "final_actions": [{"task": item["task"], "owners": item["owners"],
                           "deadline_text": item["deadline_text"], "evidence_ids": item["evidence_ids"]}
                          for item in final],
        "export_gate_open": session["omissions_checked"] and all(row["decision"] != "pending"
                                                                 for row in session["items"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
