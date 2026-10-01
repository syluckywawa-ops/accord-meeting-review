import unittest

from actionai.evaluation import score_review


class EvaluationTests(unittest.TestCase):
    def test_one_to_one_metrics_and_field_scoring(self):
        predictions = {
            "M-P001": {"owners": ["Team"], "deadline_text": "tomorrow"},
            "M-P002": {"owners": ["Project Manager"], "deadline_text": None},
        }
        gold = {
            "M-A001": {"transcript_id": "M", "owner": "Team", "deadline_text": "tomorrow"},
            "M-A002": {"transcript_id": "M", "owner": "", "deadline_text": ""},
        }
        review = [
            {"transcript_id": "M", "prediction_id": "M-P001", "human_decision": "match", "final_gold_action_id": "M-A001", "human_reason": "same task"},
            {"transcript_id": "M", "prediction_id": "M-P002", "human_decision": "no_match", "final_gold_action_id": "", "human_reason": "different task"},
        ]
        result = score_review(predictions, gold, review)
        self.assertEqual(result["task_detection"]["tp"], 1)
        self.assertEqual(result["task_detection"]["fp"], 1)
        self.assertEqual(result["task_detection"]["fn"], 1)
        self.assertEqual(result["task_detection"]["micro_f1"], 0.5)
        self.assertEqual(result["fields_on_matched_actions"]["owner_exact_accuracy"], 1.0)

    def test_duplicate_gold_match_is_rejected(self):
        predictions = {
            "M-P001": {"owners": [], "deadline_text": None},
            "M-P002": {"owners": [], "deadline_text": None},
        }
        gold = {"M-A001": {"transcript_id": "M", "owner": "", "deadline_text": ""}}
        review = [
            {"transcript_id": "M", "prediction_id": "M-P001", "human_decision": "match", "final_gold_action_id": "M-A001", "human_reason": "same"},
            {"transcript_id": "M", "prediction_id": "M-P002", "human_decision": "match", "final_gold_action_id": "M-A001", "human_reason": "same"},
        ]
        with self.assertRaises(ValueError):
            score_review(predictions, gold, review)


if __name__ == "__main__":
    unittest.main()
