# Evaluation explainer: how to read the results

## Question and comparison

The frozen experiment asks whether a single structured LLM call can extract follow-up tasks, owners, and deadlines from long meeting transcripts more accurately than an inspectable keyword-rule baseline. The three arms—rules, zero-shot LLM, and few-shot LLM—use the **same 20 untouched test meetings** and the same 45 fixed gold actions. The few-shot examples come only from the development series. The exact model, parameters, prompt/version hashes, schema, and freeze decisions are recorded in `EXPERIMENT_PROTOCOL_v1.md`, `docs/PROTOCOL_AMENDMENT_v1_1.md`, and `configs/`.

## What counts as correct

A reviewer matches predicted tasks **one-to-one within a meeting** to the same underlying work and deliverable. Paraphrase can match; a duplicate prediction cannot take a second true positive. If a prediction merges two separate gold tasks, it can match at most one. Owner and deadline quality are scored **after** task matching, so an incorrect owner does not automatically make the task a false positive. Unmatched predictions are FP; unmatched gold actions are FN. Micro precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 = 2TP/(2TP+FP+FN). All 20 meetings stay in the denominator.

The structured/evidence validator permits at most one repair. An output still invalid after repair contributes **no accepted predictions**; its gold actions become FN. This rule was fixed symmetrically before the few-shot formal run, not retrofitted to favour either arm (`docs/POST_FREEZE_TEST_EXECUTION_LOG.md`). The 20-meeting validity rate is reported separately.

## Locked results

| Method | TP | FP | FN | Precision | Recall | Micro F1 | Valid meetings | Est. API cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Keyword rules | 8 | 22 | 37 | 0.267 | 0.178 | 0.213 | 20/20 | $0 |
| Zero-shot | 24 | 50 | 21 | 0.324 | 0.533 | 0.403 | 17/20 | $0.313 |
| Few-shot | 25 | 29 | 20 | 0.463 | 0.556 | 0.505 | 17/20 | $0.275 |

The few-shot arm is best on this fixed test set, improving F1 by 0.292 over rules and 0.102 over zero-shot, but it **misses** the pre-declared 0.75 F1, 0.80 precision, and 95% valid-output gates. Among matched actions, owner sets were exactly correct for 21/25 few-shot items; explicit deadlines for 5/18. It generated one unsupported deadline among seven eligible matched actions with no gold deadline. These are not production-ready figures. The source of truth, including exact unrounded scores, token counts, latency, and review timing, is `outputs/final-analysis/final_comparison.json`.

## Files and how to inspect them

| Question | File(s) |
|---|---|
| Which meetings and gold actions? | `data/data_manifest.csv`, `data/labels/final_gold_labels.csv`, `data/labels/LABEL_VERSION.json` |
| What did each method produce? | `outputs/rule-baseline/rule-baseline-v1.0-frozen/test.json`; `outputs/llm-evaluation/{zero-shot,few-shot}-v1.0-frozen/test.json` |
| Which prediction matched which gold item, and why? | `outputs/formal-review/{rule_baseline,zero_shot,few_shot}_test_review.csv` and matching `_adjudication.json` |
| Where are final counts and secondary metrics? | `outputs/formal-review/*_test_metrics.json`, `outputs/final-analysis/final_comparison.json` |
| What was the observed human review workload? | `data/review_timing_public.md` (five-meeting observations, named reviewer, and date-correction disclosure) |
| How were predictions and scores generated? | `scripts/run_rule_baseline.py`, `scripts/run_llm_experiment.py`, `scripts/collect_formal_llm_outputs.py`, `scripts/finalize_formal_match_review.py`, `actionai/evaluation.py` |

The original paid provider logs are excluded from the public snapshot because they are large and may include provider/account metadata. The saved predictions, review decisions, metrics, versions, and code are included so that the *reported score* is auditable without repeating paid calls. Re-running a model today may yield different outputs, provider routing, availability, latency, or prices; do not replace a frozen run with a selective new call.

## Critique, not just a score

The error analysis distinguishes discussion incorrectly promoted to action, duplicates/fragments, other unsupported expansions, and plausible gold-label omissions. The last category remains FP under the fixed gold set, but warns against treating every apparent FP as a real model mistake. The 85% validity rate is an end-to-end reliability problem, not an inconvenience to hide. Deadline exactness is weak even for correctly identified tasks. Token use on long transcripts and retries also matter under a limited course API budget.

The corrected timing workbook totals 303 **net** minutes across five pre-declared meetings (60.6 per meeting). The reviewer confirmed that these sessions occurred on 29 September, after the frozen few-shot outputs were available; the workbook's original 27 September date was a recording error, transparently documented in `data/review_timing_public.md`. There was no randomised manual-only control: these observations cannot establish time saved by AI. The product's local-rule and optional Live AI import adapters have no comparable labelled test, so their outputs are demonstrations only. A future product evaluation would need a separate, representative upload dataset, more than one annotator, adjudication of disputed items, and a timed manual-only comparison before making deployment or productivity claims.

The later ES2002a product check is documented in `docs/PRODUCT_V1_1_STUDENT_REVIEW.md` with the unchanged student form and source under `data/exploratory_v11/`. The student rejected three Local rules drafts and found three missed interim assignments, but had seen the earlier assistant analysis; it was neither blinded nor timed. Do not merge its counts with the frozen three-arm metrics or the five measured review sessions.
