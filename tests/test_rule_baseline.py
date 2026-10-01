import json
import unittest
from pathlib import Path

from actionai.rule_baseline import extract_actions, jaccard


ROOT = Path(__file__).parents[1]
CONFIG = json.loads((ROOT / "configs/rule_baseline_v1.json").read_text())


def payload(turns):
    return {"turns": turns}


class RuleBaselineTests(unittest.TestCase):
    def test_late_self_commitment_is_extracted(self):
        turns = [
            {"turn_id": f"M-T{i:04d}", "role": "Project Manager", "text": "Discussion."}
            for i in range(1, 5)
        ]
        turns.append(
            {
                "turn_id": "M-T0005",
                "role": "Project Manager",
                "text": "I'll write up the notes and send them to everybody.",
            }
        )
        actions = extract_actions(payload(turns), CONFIG)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["owners"], ["Project Manager"])
        self.assertEqual(actions[0]["rule_id"], "self_commitment")

    def test_early_product_idea_is_not_action(self):
        turns = [
            {
                "turn_id": "M-T0001",
                "role": "Project Manager",
                "text": "We're gonna design a new remote control.",
            },
            *[
                {"turn_id": f"M-T{i:04d}", "role": "Marketing Expert", "text": "Discussion."}
                for i in range(2, 9)
            ],
        ]
        self.assertEqual(extract_actions(payload(turns), CONFIG), [])

    def test_late_meeting_management_phrase_is_not_action(self):
        turns = [
            {"turn_id": f"M-T{i:04d}", "role": "Project Manager", "text": "Discussion."}
            for i in range(1, 4)
        ]
        turns.append(
            {
                "turn_id": "M-T0004",
                "role": "Project Manager",
                "text": "I'll just start at the top of this agenda.",
            }
        )
        self.assertEqual(extract_actions(payload(turns), CONFIG), [])

    def test_collective_deadline_is_retained(self):
        turns = [
            {"turn_id": f"M-T{i:04d}", "role": "Project Manager", "text": "Discussion."}
            for i in range(1, 4)
        ]
        turns.append(
            {
                "turn_id": "M-T0004",
                "role": "Project Manager",
                "text": "We have thirty minutes until the next meeting, so we'll have to decide the basic functionality.",
            }
        )
        actions = extract_actions(payload(turns), CONFIG)
        self.assertEqual(actions[0]["owners"], ["Team"])
        self.assertIn("next meeting", actions[0]["deadline_text"])

    def test_jaccard_supports_deterministic_deduplication(self):
        self.assertGreaterEqual(jaccard("create a clay prototype", "work on prototype using clay"), 0.40)
        self.assertEqual(jaccard("send notes", "evaluate product"), 0.0)


if __name__ == "__main__":
    unittest.main()
