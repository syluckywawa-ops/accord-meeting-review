import json
import unittest
from pathlib import Path

from actionai.output_validation import parse_and_validate, validate_complete_input, validate_output


METADATA = {
    "meeting_id": "ES2003a",
    "turns": [
        {
            "turn_id": "ES2003a-T0001",
            "text": "I'll write the meeting notes tomorrow.",
        }
    ],
}


def valid_payload():
    return {
        "action_items": [
            {
                "task": "write the meeting notes",
                "owners": ["Project Manager"],
                "deadline_text": "tomorrow",
                "deadline_normalized": None,
                "evidence_text": "I'll write the meeting notes tomorrow.",
                "evidence_ids": ["ES2003a-T0001"],
                "needs_review": False,
                "review_reason": None,
            }
        ]
    }


class OutputValidationTests(unittest.TestCase):
    def test_provider_schema_avoids_unsupported_keywords(self):
        root = Path(__file__).parents[1]
        schema_text = (root / "schemas/action_output_v1.schema.json").read_text()
        schema = json.loads(schema_text)
        encoded = json.dumps(schema)
        self.assertNotIn('"uniqueItems"', encoded)
        self.assertNotIn('"oneOf"', encoded)

    def test_provider_schema_requires_every_object_property(self):
        root = Path(__file__).parents[1]
        schema = json.loads((root / "schemas/action_output_v1.schema.json").read_text())

        def check(node):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertEqual(set(node.get("properties", {})), set(node.get("required", [])))
                for value in node.values():
                    check(value)
            elif isinstance(node, list):
                for value in node:
                    check(value)

        check(schema)

    def test_valid_supported_output(self):
        self.assertEqual(validate_output(valid_payload(), METADATA), [])

    def test_malformed_json_is_rejected(self):
        payload, issues = parse_and_validate('{"action_items": [}', METADATA)
        self.assertIsNone(payload)
        self.assertTrue(any(issue.location == "json" for issue in issues))

    def test_unsupported_evidence_is_rejected(self):
        payload = valid_payload()
        payload["action_items"][0]["evidence_text"] = "I will invent a deadline."
        issues = validate_output(payload, METADATA)
        self.assertTrue(any("not verbatim" in issue.message for issue in issues))

    def test_unknown_owner_is_rejected(self):
        payload = valid_payload()
        payload["action_items"][0]["owners"] = ["Ben"]
        issues = validate_output(payload, METADATA)
        self.assertTrue(any("Unsupported owners" in issue.message for issue in issues))

    def test_missing_owner_requires_review_flag(self):
        payload = valid_payload()
        payload["action_items"][0]["owners"] = []
        issues = validate_output(payload, METADATA)
        self.assertTrue(any("Missing owner" in issue.message for issue in issues))

    def test_no_silent_truncation(self):
        self.assertEqual(validate_complete_input("complete", "complete"), [])
        self.assertTrue(validate_complete_input("complete", "complete"[:-1]))


if __name__ == "__main__":
    unittest.main()
