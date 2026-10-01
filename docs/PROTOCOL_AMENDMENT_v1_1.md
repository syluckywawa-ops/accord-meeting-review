# ActionAI protocol amendment v1.1

**Date:** 27 September 2026  
**Scope:** Decisions resolved after gold-label lock and before any formal test output.

## Frozen rule baseline

`rule-baseline-v1.0-frozen` was frozen before any test execution. Its code, configuration, development predictions, human match review, development metrics, and gold-label CSV are recorded by SHA-256 in `configs/RULE_BASELINE_VERSION.json`.

Development diagnostics after confirmed one-to-one semantic review were 6 TP, 2 FP, 0 FN, micro precision 0.750, recall 1.000, F1 0.857, and macro F1 0.833. These values are not formal test results.

## LLM and provider candidate

- Provider: OpenRouter.
- Exact model ID: `openai/gpt-4.1-mini-2025-04-14`.
- Context window: 1,047,576 tokens.
- Listed price checked 27 September 2026: USD 0.40 per million input tokens and USD 1.60 per million output tokens.
- Temperature: 0.
- Maximum output: 4,096 tokens.
- Structured output: strict JSON Schema with `provider.require_parameters=true`.
- Tokenizer used for local preflight: `o200k_base`; actual provider usage will replace estimates in final reporting.
- Truncation: prohibited.
- Retry: at most one repair attempt, only after JSON/schema/evidence validation failure; the retry and its full usage are logged.

Official sources:

- OpenRouter model and listed price: https://openrouter.ai/openai/gpt-4.1-mini-2025-04-14/pricing
- OpenRouter structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs

The LLM configuration remains marked `dev` until both arms pass development dry runs. Model selection may not change in response to locked test performance.

The first development requests exposed provider-schema compatibility errors: the strict structured-output subset rejected JSON Schema's `uniqueItems` and `oneOf` keywords and required every declared object property to appear in `required`. Unsupported keywords were replaced with supported schema forms, and the baseline-only `rule_id` diagnostic was removed from the transmitted shared schema before any valid model output was produced. Duplicate owners/evidence IDs and ISO deadline syntax remain checked by the local validator. These development-only compatibility corrections do not alter the task definition, examples, data, scoring rule, or test set.

## Output-contract amendment

Protocol v1 listed `evidence_text` but not an evidence identifier in the model output. Version 1.1 additionally requires an `evidence_ids` array containing the exact AMI turn IDs. This is a safeguard, not an outcome-driven change: it permits automatic verification that every quoted span occurs verbatim in the cited source turn. The same comparison fields are used for the rule, zero-shot, and few-shot arms. The deterministic baseline may retain `rule_id` only in its raw diagnostic artifact; it is outside the shared LLM schema and ignored during comparative scoring.

## Prompt conditions

- Zero-shot uses the task definition, safety instructions, output schema, and complete transcript, with no labelled examples.
- Few-shot uses the identical system instruction, schema, model, parser, retry policy, and transcript formatting, plus three compact examples drawn only from the declared development series `ES2003`.
- The examples include a self-commitment with no deadline, a joint assignment with a relative deadline, and a non-action product statement.
- Transcript content is delimited as untrusted quoted data and cannot override system instructions.

## Token and budget preflight

The local model-tokenizer preflight covers 23 meetings × 2 LLM conditions = 46 calls:

- estimated input tokens: 791,637;
- reserved maximum output tokens: 188,416;
- estimated input cost: USD 0.3167;
- worst-case reserved output cost: USD 0.3015;
- conservative total: USD 0.6182;
- non-processable meetings: 0;
- largest prompt plus output reserve: approximately 3.67% of the declared context window.

The preflight therefore passes the USD 10 gate with substantial margin. These are conservative planning values, not actual billed usage.

## Still unresolved before formal testing

- Frozen LLM configuration and prompt hashes.
- Five pre-declared test meetings for descriptive review timing.
- Final test-execution authorization after every freeze-gate check passes.

## Development prompt revision log

The initial zero-shot development pass produced one valid output for `ES2003a`, one valid but over-inclusive output for `ES2003b`, and an invalid output for `ES2003c` after one repair. The invalid response wrapped evidence spans in quotation marks and appended turn IDs, so the spans were no longer verbatim substrings. It also treated several design decisions as follow-up assignments. Before rerunning any test meeting, the system prompt was clarified to (1) exclude product decisions and preferences unless concrete follow-up work is explicitly assigned, (2) prohibit assigning ownership merely from discussion participation, and (3) require evidence text with no quotation wrappers, labels, parenthesized IDs, ellipses, or cleaned disfluencies. The repair instruction received the same evidence-format clarification. The initial outputs were retained under `outputs/raw_api/archive/zero_shot_initial_2026-09-28/` rather than deleted.

The first revised `ES2003c` run reduced evidence failures but remained invalid after the one permitted repair and remained semantically over-inclusive. Its output was retained under `outputs/raw_api/archive/zero_shot_revision1_2026-09-28/`. A second development-only revision required explicit commitment evidence rather than task-like product language. For an evidence-format retry, the deterministic pipeline now supplies the exact text of the model's cited source turns, allowing correction without relaxing verbatim validation or increasing the one-retry limit.

The second revised `ES2003c` run became structurally valid but remained over-inclusive: it treated product design decisions and immediate meeting operations as post-meeting actions and missed one closing self-commitment. That output was retained under `outputs/raw_api/archive/zero_shot_revision2_2026-09-28/`. The final planned development revision therefore distinguishes work performed after the current meeting from in-meeting operations, treats an explicit closing allocation as authoritative when present, uses earlier discussion only for clarification, carries an allocation deadline into the immediately summarized tasks where supported, and prevents the assigning speaker from being treated automatically as the addressee in “you/yourself and [role]” language. All three development meetings must be rerun under this single prompt hash before prompt freeze.

The final zero-shot development rerun produced structurally valid outputs for all three meetings under the same prompt assets. Human one-to-one semantic review against the current locked gold labels recorded 4 TP, 9 apparent FP, and 2 FN: micro precision 0.308, recall 0.667, F1 0.421, and macro F1 0.500. Owner-set exact accuracy on the four matched actions was 3/4; deadline exact accuracy was 0/2. The three calls required one repair retry each and cost approximately USD 0.0351 in total.

These development metrics are conditional on the current gold labels. The nine unmatched predictions are not treated as a single error type: review identified clear discussion-to-action promotions, one duplicate extraction under one-to-one matching, and several plausible actions that may be absent from the current gold set. They remain false positives for the locked quantitative evaluation, preserving comparability and avoiding outcome-driven relabelling, but the final qualitative analysis must call them **apparent false positives** and disclose this annotation limitation. No additional zero-shot prompt tuning will be performed from these outputs.

The few-shot development run then produced three valid outputs with no repair retries and an estimated total API cost of USD 0.0163. Human review against the same fixed gold labels recorded 3 TP, 5 apparent FP, and 3 FN: micro precision 0.375, recall 0.500, F1 0.429, and macro F1 0.484. Compared with zero-shot, the micro F1 increase was approximately 0.008, while the number of predictions fell from 13 to 8. Few-shot missed `ES2003a-A002`, `ES2003c-A001`, and `ES2003c-A002`.

Qualitative adjudication classified two apparent false positives as probable ES2003b gold-label omissions, two as duplicate or fragmented extractions, and one as a soft design suggestion incorrectly promoted to a standalone action. The fixed-gold quantitative result is retained without post-output relabelling. Because the few-shot examples were intentionally drawn from the development series and include exact development passages, this score is an in-sample prompt diagnostic rather than an unbiased estimate. Only the locked unseen test set will support the formal comparison.
