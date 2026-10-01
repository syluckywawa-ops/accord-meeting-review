import copy
import unittest
from actionai.review_workspace import new_session, apply_review, approved_items, export_csv, task_tracking, review_hints


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {"meeting_id": "TS3003c", "turns": [{"turn_id": "TS3003c-T0001", "text": "I will write the minutes."}]}
        self.item = {"task": "write minutes", "owners": ["Project Manager"], "deadline_text": None,
                     "deadline_normalized": None, "evidence_text": "I will write the minutes.",
                     "evidence_ids": ["TS3003c-T0001"], "needs_review": False, "review_reason": None}
        self.session = new_session("TS3003c", "few_shot", {"run_status": "valid", "action_items": [self.item]})

    def test_export_requires_both_decision_and_scan(self):
        with self.assertRaises(ValueError):
            approved_items(self.session, self.metadata)
        state = apply_review(self.session, {"action": "accept", "id": "candidate-1"}, self.metadata)
        with self.assertRaises(ValueError):
            approved_items(state, self.metadata)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, self.metadata)
        self.assertEqual(len(approved_items(state, self.metadata)), 1)
        state = apply_review(state, {"action": "reopen", "id": "candidate-1"}, self.metadata)
        self.assertFalse(state["omissions_checked"])

    def test_invalid_source_drops_predictions_and_allows_manual_reconstruction(self):
        state = new_session("TS3003c", "few_shot", {"run_status": "invalid", "action_items": [self.item]})
        self.assertEqual(state["items"], [])
        state = apply_review(state, {"action": "add", "item": self.item}, self.metadata)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, self.metadata)
        self.assertEqual(len(approved_items(state, self.metadata)), 1)

    def test_bad_evidence_rejected_without_state_mutation(self):
        item = copy.deepcopy(self.item)
        item["evidence_text"] = "unrelated fabricated quote"
        with self.assertRaises(ValueError):
            apply_review(self.session, {"action": "edit", "id": "candidate-1", "item": item}, self.metadata)
        self.assertEqual(self.session["revision"], 0)
        self.assertEqual(self.session["history"], [])

    def test_rejected_candidates_never_export_and_original_survives_edit(self):
        item = copy.deepcopy(self.item)
        item["task"] = "prepare meeting minutes"
        state = apply_review(self.session, {"action": "edit", "id": "candidate-1", "item": item}, self.metadata)
        self.assertEqual(state["items"][0]["original"]["task"], "write minutes")
        state = apply_review(state, {"action": "reject", "id": "candidate-1"}, self.metadata)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, self.metadata)
        self.assertEqual(approved_items(state, self.metadata), [])

    def test_csv_protects_formula_text(self):
        item = dict(self.item, task="=1+1")
        self.assertIn("'=1+1", export_csv([item]))

    def test_completion_is_reversible_audited_and_preserves_export_gate(self):
        state = apply_review(self.session, {"action": "accept", "id": "candidate-1"}, self.metadata)
        state = apply_review(state, {"action": "confirm_scan", "value": True}, self.metadata)
        completed = apply_review(state, {"action": "set_completed", "id": "candidate-1", "value": True}, self.metadata)
        self.assertTrue(completed["omissions_checked"])
        self.assertTrue(completed["items"][0]["completed"])
        self.assertIsNotNone(completed["items"][0]["completed_at"])
        self.assertFalse(state["items"][0]["completed"])
        self.assertEqual(approved_items(completed, self.metadata), [self.item])
        self.assertTrue(completed["history"][-1]["after"]["completed"])
        self.assertIn("completed_at", export_csv([self.item], task_tracking(completed)))
        restored = apply_review(completed, {"action": "set_completed", "id": "candidate-1", "value": False}, self.metadata)
        self.assertFalse(restored["items"][0]["completed"])
        self.assertIsNone(restored["items"][0]["completed_at"])

    def test_completion_cannot_bypass_approval_or_accept_non_boolean(self):
        with self.assertRaises(ValueError):
            apply_review(self.session, {"action": "set_completed", "id": "candidate-1", "value": True}, self.metadata)
        state = apply_review(self.session, {"action": "accept", "id": "candidate-1"}, self.metadata)
        for value in ("false", 1, None):
            with self.assertRaises(ValueError):
                apply_review(state, {"action": "set_completed", "id": "candidate-1", "value": value}, self.metadata)
        rejected = apply_review(state, {"action": "reject", "id": "candidate-1"}, self.metadata)
        with self.assertRaises(ValueError):
            apply_review(rejected, {"action": "set_completed", "id": "candidate-1", "value": True}, self.metadata)

    def test_edit_or_revoke_resets_completion_and_legacy_defaults(self):
        state = apply_review(self.session, {"action": "accept", "id": "candidate-1"}, self.metadata)
        state["items"][0].pop("completed")
        state["items"][0].pop("completed_at")
        self.assertFalse(task_tracking(state)[0]["completed"])
        done = apply_review(state, {"action": "set_completed", "id": "candidate-1", "value": True}, self.metadata)
        for action in ("edit", "reject", "reopen"):
            changed = apply_review(done, {"action": action, "id": "candidate-1", "item": self.item}, self.metadata)
            self.assertFalse(changed["items"][0]["completed"])
            self.assertIsNone(changed["items"][0]["completed_at"])

    def test_advisory_hints_do_not_modify_or_block_a_review(self):
        duplicate = dict(self.item, task="write minutes for the group")
        vague = dict(self.item, task="check the proposal", evidence_text="I will write the minutes.")
        state = new_session("TS3003c", "few_shot", {"run_status": "valid", "action_items": [self.item, duplicate, vague]})
        original = copy.deepcopy(state)
        hints = review_hints(state)
        self.assertEqual(state, original)
        self.assertEqual([h["code"] for h in hints["candidate-1"]], ["thin_evidence"])
        self.assertNotIn("possible_duplicate", [h["code"] for h in hints["candidate-2"]])
        self.assertIn("thin_evidence", [h["code"] for h in hints["candidate-3"]])
        state = apply_review(state, {"action": "reject", "id": "candidate-3"}, self.metadata)
        self.assertEqual(review_hints(state)["candidate-3"], [])
