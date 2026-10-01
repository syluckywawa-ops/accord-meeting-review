import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from actionai.imported_meetings import prepare_import, extract_rules, extract_llm, validate_review
from actionai.review_workspace import new_session, apply_review, approved_items, review_hints


class ImportedMeetingTests(unittest.TestCase):
    def test_v11_exploratory_review_flow_on_constructed_fictional_meeting(self):
        text = (Path(__file__).parent / "fixtures/v11_review_trial.txt").read_text()
        meta = prepare_import(text, "V1.1 constructed fictional trial")
        result = extract_rules(meta)
        self.assertEqual(len(result["action_items"]), 4)
        state = new_session(meta["meeting_id"], "local_rules", result)
        hints = review_hints(state)
        self.assertIn("possible_duplicate", [h["code"] for h in hints["candidate-1"]])
        self.assertIn("possible_duplicate", [h["code"] for h in hints["candidate-3"]])
        self.assertEqual(hints["candidate-2"], [])
        self.assertIn("thin_evidence", [h["code"] for h in hints["candidate-4"]])

        for candidate_id, deadline in (("candidate-1", "by Friday"), ("candidate-2", "tomorrow")):
            corrected = copy.deepcopy(state["items"][int(candidate_id[-1]) - 1]["current"])
            corrected["deadline_text"] = deadline
            state = apply_review(state, {"action": "edit", "id": candidate_id, "item": corrected}, meta)
        for candidate_id in ("candidate-3", "candidate-4"):
            state = apply_review(state, {"action": "reject", "id": candidate_id}, meta)
        with self.assertRaises(ValueError):
            approved_items(state, meta)
        missed = {
            "task": "update the risk log", "owners": ["Jamie"],
            "deadline_text": "by Monday", "deadline_normalized": None,
            "evidence_text": "Jamie, please update the risk log by Monday. || Yes, I can update the risk log by Monday.",
            "evidence_ids": [meta["turns"][4]["turn_id"], meta["turns"][5]["turn_id"]],
            "needs_review": False, "review_reason": None,
        }
        state = apply_review(state, {"action": "add", "item": missed}, meta)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, meta)
        final = approved_items(state, meta)
        self.assertEqual(len(final), 3)
        self.assertIn("update the risk log", [item["task"] for item in final])
        self.assertEqual([item["deadline_text"] for item in final], ["by Friday", "tomorrow", "by Monday"])
        self.assertEqual(len(state["history"]), 6)

    def test_new_meeting_names_quotes_and_export(self):
        meta = prepare_import("Alex: I will send the proposal by Friday.\nJamie: We could change the colour.", "Project update")
        result = extract_rules(meta)
        self.assertEqual(len(result["action_items"]), 1)
        self.assertEqual(result["action_items"][0]["owners"], ["Alex"])
        self.assertEqual(validate_review({"action_items": result["action_items"]}, meta), [])
        state = new_session(meta["meeting_id"], "local_rules", result)
        state = apply_review(state, {"action": "accept", "id": "candidate-1"}, meta)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, meta)
        self.assertEqual(len(approved_items(state, meta)), 1)

    def test_foreign_evidence_rejected(self):
        meta = prepare_import("Alex: I'll send the slides.", "Demo")
        other = prepare_import("Alex: I'll send the slides.", "Other")
        result = extract_rules(other)
        self.assertTrue(validate_review({"action_items": result["action_items"]}, meta))

    def test_missing_speaker_is_flagged(self):
        meta = prepare_import("我会发送会议纪要。", "中文会议")
        item = extract_rules(meta)["action_items"][0]
        self.assertEqual(item["owners"], [])
        self.assertTrue(item["needs_review"])

    def test_empty_and_oversize_rejected(self):
        for text in ("  ", "x" * 150001):
            with self.assertRaises(ValueError):
                prepare_import(text, "Invalid")

    def test_live_import_accepts_real_participant_name_without_network(self):
        meta = prepare_import("Alex: I will send the checklist by Friday.", "Mock live import")
        payload = {"action_items": [{
            "task": "send the checklist",
            "owners": ["Alex"],
            "deadline_text": "by Friday",
            "deadline_normalized": None,
            "evidence_text": "I will send the checklist by Friday.",
            "evidence_ids": [meta["turns"][0]["turn_id"]],
            "needs_review": False,
            "review_reason": None,
        }]}
        calls = []

        def completion(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                id="mock-response", model="mock-model",
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
                usage=SimpleNamespace(prompt_tokens=30, completion_tokens=20, total_tokens=50),
            )

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-only"}), patch("openai.OpenAI", return_value=client):
            result = extract_llm(meta, "live_ai", Path(__file__).resolve().parents[1])
        self.assertEqual(result["run_status"], "valid")
        self.assertEqual(result["action_items"][0]["owners"], ["Alex"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["usage"]["input_tokens"], 30)
        self.assertEqual(result["usage"]["output_tokens"], 20)
