import json
import unittest
from types import SimpleNamespace

from actionai.llm_pipeline import evidence_repair_context, execute_extraction, response_format


METADATA = {
    "meeting_id": "ES2003a",
    "turns": [{"turn_id": "ES2003a-T0001", "text": "I'll send the notes."}],
}
SCHEMA = {"type": "object", "properties": {"action_items": {"type": "array"}}, "required": ["action_items"]}
CONFIG = {
    "model": "test-model",
    "temperature": 0,
    "max_output_tokens": 100,
    "provider_require_parameters": True,
    "maximum_schema_repair_retries": 1,
    "input_usd_per_million_tokens": 1.0,
    "output_usd_per_million_tokens": 2.0,
}


def valid_content():
    return json.dumps(
        {
            "action_items": [
                {
                    "task": "send the notes",
                    "owners": ["Project Manager"],
                    "deadline_text": None,
                    "deadline_normalized": None,
                    "evidence_text": "I'll send the notes.",
                    "evidence_ids": ["ES2003a-T0001"],
                    "needs_review": False,
                    "review_reason": None,
                }
            ]
        }
    )


class FakeCompletions:
    def __init__(self, contents):
        self.contents = list(contents)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.contents.pop(0)
        return SimpleNamespace(
            id=f"response-{len(self.calls)}",
            model="resolved-test-model",
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        )


class LLMPipelineTests(unittest.TestCase):
    def test_evidence_repair_context_supplies_exact_cited_turn(self):
        payload = {
            "action_items": [
                {"evidence_ids": ["ES2003a-T0001"], "evidence_text": "cleaned quote"}
            ]
        }
        issues = [SimpleNamespace(location="action_items[0].evidence_text", message="Evidence is not verbatim")]
        context = evidence_repair_context(payload, issues, METADATA)
        self.assertIn("ES2003a-T0001: I'll send the notes.", context)
        self.assertIn("exact contiguous substring", context)

    def test_schema_repair_retries_once(self):
        completions = FakeCompletions(["not json", valid_content()])
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        result = execute_extraction(
            client=client,
            config=CONFIG,
            schema=SCHEMA,
            messages=[{"role": "user", "content": "extract"}],
            metadata=METADATA,
        )
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(len(completions.calls), 2)
        repair_message = completions.calls[1]["messages"][-1]["content"]
        self.assertIn("no parenthesized turn ID", repair_message)

    def test_valid_first_response_uses_one_call(self):
        completions = FakeCompletions([valid_content()])
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        result = execute_extraction(
            client=client,
            config=CONFIG,
            schema=SCHEMA,
            messages=[{"role": "user", "content": "extract"}],
            metadata=METADATA,
        )
        self.assertEqual(result["retry_count"], 0)
        self.assertEqual(len(completions.calls), 1)
        self.assertEqual(result["usage_total"]["input_tokens"], 100)


if __name__ == "__main__":
    unittest.main()
