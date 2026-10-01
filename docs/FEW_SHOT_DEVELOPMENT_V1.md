# Few-shot development evaluation

**Status:** reviewed and accepted on 28 September 2026  
**Scope:** three development meetings only; in-sample prompt diagnostic, not a formal test result.

## Quantitative result against the current gold labels

| Measure | Result |
|---|---:|
| True positives | 3 |
| Apparent false positives | 5 |
| False negatives | 3 |
| Micro precision | 0.375 |
| Micro recall | 0.500 |
| Micro F1 | 0.429 |
| Macro F1 | 0.484 |
| Owner-set exact accuracy on matched actions | 3/3 (1.000) |
| Deadline exact accuracy on eligible matched actions | 1/1 (1.000) |
| Predictions | 8 |
| Repair retries | 0 |
| API cost | approximately USD 0.0163 |

The system missed `ES2003a-A002`, `ES2003c-A001`, and `ES2003c-A002`.

## Qualitative interpretation

Against the current gold labels, few-shot achieved F1 = 0.429. Its apparent false positives include two probable gold-label omissions, two duplicate or fragmented extractions, and one soft design suggestion incorrectly promoted to a standalone action item.

The two probable omissions are `ES2003b-P001`, for which the Industrial Designer restates the requested transmitter, speaker, and LED investigation, and `ES2003b-P004`, where a direct feedback-gathering request is present. `ES2003b-P002` fragments the broader component-feasibility investigation, while `ES2003b-P005` duplicates the transmitter task. `ES2003b-P006` is the clearest model error because the wording describes something the designer might consider rather than an independent committed deliverable.

For reproducible scoring, all five unmatched predictions remain false positives and the gold labels remain unchanged. The potential incompleteness of the ES2003b labels is disclosed as an evaluation limitation rather than corrected after seeing model outputs.

## Development-data caveat

The few-shot examples were drawn from the declared ES2003 development series and include exact passages used in this diagnostic evaluation. Therefore, this development score is not an unbiased generalisation estimate and must not be presented as the main performance result. The locked unseen test set will provide the formal comparison among the rule baseline, zero-shot, and few-shot systems.

## Reproducible evidence

- Aggregated predictions: `outputs/llm-evaluation/few-shot-v1.0-dev/development.json`
- Accepted human review: `outputs/llm-evaluation/few-shot-v1.0-dev/development_match_review.csv`
- Metrics: `outputs/llm-evaluation/few-shot-v1.0-dev/development_metrics.json`
- Per-call audit logs: `outputs/raw_api/llm-experiment-v1.0-dev/few_shot/development/`
