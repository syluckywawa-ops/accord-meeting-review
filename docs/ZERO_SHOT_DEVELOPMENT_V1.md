# Zero-shot development evaluation

**Status:** reviewed and accepted on 28 September 2026  
**Scope:** three development meetings only; these are diagnostics, not formal test results.

## Quantitative result against the current gold labels

| Measure | Result |
|---|---:|
| True positives | 4 |
| Apparent false positives | 9 |
| False negatives | 2 |
| Micro precision | 0.308 |
| Micro recall | 0.667 |
| Micro F1 | 0.421 |
| Macro F1 | 0.500 |
| Owner-set exact accuracy on matched actions | 3/4 (0.750) |
| Deadline exact accuracy on eligible matched actions | 0/2 (0.000) |
| Final-run API cost | approximately USD 0.0351 |

## Interpretation boundary

The score is calculated against the current locked gold labels and can be reported as the reproducible quantitative result. However, the nine unmatched predictions are heterogeneous. They include discussion-to-action errors, a duplicate extraction, and plausible actions that are not represented in the current gold set. Consequently, they remain false positives for quantitative scoring but should be described as **apparent false positives** in qualitative analysis. It would be inaccurate to claim that all nine arose because the model converted discussion into action.

The gold labels will not be modified after inspecting model outputs. This preserves the pre-declared evaluation and prevents outcome-driven relabelling. Potential gold omissions will instead be disclosed as a limitation and illustrated with evidence in the final error analysis.

## Reproducible evidence

- Aggregated predictions: `outputs/llm-evaluation/zero-shot-v1.0-dev/development.json`
- Accepted human review: `outputs/llm-evaluation/zero-shot-v1.0-dev/development_match_review.csv`
- Metrics: `outputs/llm-evaluation/zero-shot-v1.0-dev/development_metrics.json`
- Per-call audit logs: `outputs/raw_api/llm-experiment-v1.0-dev/zero_shot/development/`

No further zero-shot prompt tuning will be performed from these development outputs. The next experimental step is the few-shot development arm using the same model, schema, parser, retry policy, and transcript formatting.
