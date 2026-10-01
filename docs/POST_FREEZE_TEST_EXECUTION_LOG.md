# Post-freeze formal test execution log

This file records events after the experiment freeze. It does not modify the frozen model, prompts, schema, parser, retry policy, labels, or matching rule.

## Zero-shot formal test execution — 28 September 2026

- Frozen version: `llm-experiment-v1.0-frozen`
- Planned meetings: 20
- Saved meeting logs: 20
- Valid after at most one repair: 17
- Invalid after the permitted repair: 3
- Validation success rate: 17/20 = 0.850
- Invalid meetings: `ES2014d`, `TS3007b`, `TS3007c`
- Total estimated API cost: USD 0.312796
- Selective reruns: none

The invalid outputs were returned by the provider and parsed, but failed the frozen local evidence validation after the single permitted repair. They remain preserved in the raw audit logs and will not be selectively rerun.

## Invalid-output scoring rule fixed before few-shot test execution

The original protocol rejects outputs that fail the frozen JSON, schema, or evidence validator and permits only one repair. It did not explicitly state how an output still invalid after that repair enters task-level F1. The following conservative operational rule is fixed now, before running the formal few-shot arm, and applies symmetrically to both LLM conditions:

1. An invalid output supplies no accepted predictions for the primary end-to-end score.
2. Every gold action in that meeting is therefore unmatched and contributes a false negative.
3. The validation-success rate and identities of failed meetings are reported separately as reliability and coverage outcomes.
4. Parsed content from invalid logs may be discussed qualitatively but is not repaired manually or credited in the primary score.
5. A secondary valid-meetings-only diagnostic may be reported only with an explicit denominator and must not replace the primary all-test score.

This rule prevents invalid structured output from receiving selective manual repair and prevents outcome-dependent reruns. The fixed gold labels remain unchanged.

## Few-shot formal test execution — 28 September 2026

- Frozen version: `llm-experiment-v1.0-frozen`
- Planned meetings: 20
- Saved meeting logs: 20
- Valid after at most one repair: 17
- Invalid after the permitted repair: 3
- Validation success rate: 17/20 = 0.850
- Invalid meetings: `ES2004d`, `IS1009a`, `IS1009b`
- Total estimated API cost: USD 0.2749836
- Selective reruns: none

The previously fixed invalid-output scoring rule applies unchanged. The raw invalid logs remain preserved for reliability and qualitative analysis.

## Rule-baseline formal test execution — 28 September 2026

- Frozen version: `rule-baseline-v1.0-frozen`
- Meetings: 20
- Predictions: 30
- Network calls and API cost: 0
- Output: `outputs/rule-baseline/rule-baseline-v1.0-frozen/test.json`

All three formal arms have now been executed. No further model calls are required for the primary experiment.
