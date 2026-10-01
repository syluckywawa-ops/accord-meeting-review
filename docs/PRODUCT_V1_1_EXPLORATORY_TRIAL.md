# Accord v1.1: small product iteration and exploratory check

**Date:** 2 October 2026. This is a post-experiment product refinement, not a new formal model arm. It does not alter the 23 AMI transcripts, locked gold labels, saved predictions, prompts, or reported F1.

## Why this change

The frozen few-shot test produced 25 matched actions, 29 unmatched predictions, and 20 missed gold actions. Six of its unmatched predictions were tagged duplicate/fragment, while some predictions cited a short quote that needed adjacent turns to establish the actual task. These observations motivate a *review aid*, not an automatic correction. A reviewer still needs to compare the original utterances and scan for omissions.

## What v1.1 adds

- `review_hints()` computes advisory messages from the **current review session**, separately from extraction and scoring. Two non-rejected model candidates are marked *possibly overlapping* when their non-trivial task word sets have substantial overlap or one is a fragment of the other. This is a heuristic, not a semantic-match verdict; distinct but related tasks may be flagged and paraphrased duplicates may be missed.
- A quote shorter than six words, or a short quote with a referent such as “that” or “it”, receives a *check surrounding turns* message. Exact-quote validation remains unchanged. A brief quote can still be sufficient, and a long quote can still be misleading.
- The UI shows the number of pending candidates with advisory messages and makes the full-transcript omission scan more prominent. No candidate is automatically rejected, reordered in the exported list, or given an invented confidence score. The existing accept/edit/reject/add and scan-before-export gates remain in force.

## Separate fictional workflow check

The new seven-turn fixture is `tests/fixtures/v11_review_trial.txt`. It was written specifically to exercise the review workflow; it is **not** an unseen real-world benchmark and was not used to recompute the formal scores. It contains two repeated budget commitments, a figures review, an unaccepted colour suggestion, a request and acceptance to update a risk log, and a vague “I will check that.”

| Step | Observed result |
|---|---|
| Local-rule import | Four drafts: budget twice, figures once, vague check once. The cross-speaker risk-log assignment was missed; the unaccepted colour suggestion was not drafted. |
| Advisory checks | The two budget drafts were marked as possibly overlapping; the vague check was marked as context-dependent. The clear figures commitment was not flagged after a conservative threshold adjustment. |
| Human review | Two useful drafts were edited to restore their stated deadlines; the duplicate and vague draft were rejected; the omitted risk-log action was added with both request and acceptance turns as evidence. |
| Export gate | Export remained disabled until all drafts had a decision and the full transcript scan was confirmed. Editing an approved draft reset the scan confirmation. Final reviewed list: three actions with the supported deadline phrases. |

The complete case is exercised in `tests/test_imported_meetings.py` and browser-checked through the local interface. The full suite passes 55 tests. This verifies expected behaviour for one deliberately constructed case, **not** detection rates, general accuracy, time saved, or a usable production threshold. There was no independent reviewer or manual-only timed comparison. A next-stage evaluation would require new representative meetings, blinded human adjudication of hint quality, and a comparison of assisted versus manual-only review time and final-list correctness.

A later one-meeting check using public AMI transcript ES2002a, outside the frozen 23-meeting sample, is documented separately in [the real-meeting review note](PRODUCT_V1_1_REAL_MEETING_CHECK.md). Its three rejected drafts and three manually added actions underline the same limitation: the hints do not remove the need for full source review.

## Report-safe conclusion

“After freezing the three-arm experiment, I added a small advisory layer to Accord: it highlights possible duplicate tasks and context-poor evidence and keeps an explicit full-transcript omission check. In a separate seven-turn fictional workflow test, the reviewer could remove a duplicate, correct two omitted deadline fields, add one missed assignment, and export three evidence-supported actions. This demonstrates the review workflow, not an improvement in the locked F1 or a measured productivity gain.”
