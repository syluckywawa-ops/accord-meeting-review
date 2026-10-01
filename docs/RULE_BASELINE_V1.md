# Keyword-rule baseline v1 — development record

## Purpose

This is the deliberately simple, deterministic comparison arm for ActionAI. It uses no model, network call, randomness, official AMI action summary, or test-set result. Rules were developed only with the three declared development meetings (`ES2003a`, `ES2003b`, and `ES2003c`).

## Frozen logic

The baseline searches only the closing quarter of each meeting, where follow-up work is commonly assigned. It detects:

1. first-person commitments such as “I’ll …”, “I can …”, and “I’d better …”;
2. direct requests such as “if you could …”;
3. explicit second-person assignments such as “you’re going to …”;
4. collective obligations tied to the next meeting; and
5. joint prototype assignments where both roles and the deliverable occur in adjacent turns.

It excludes a short, documented list of immediate meeting-management phrases. Owners are taken from the speaker for self-commitments, from explicit role mentions, or inferred from nearby speaker context and flagged for review. Deadline phrases are copied from a small fixed dictionary; dates are never invented. Near-duplicate candidates are resolved deterministically using token overlap and rule priority.

## Leakage control

`scripts/run_rule_baseline.py` defaults to the development split. A test run is refused unless the explicit `--allow-test` switch is supplied. That switch must not be used until the full experiment freeze gate has passed. The development run stores the configuration hash and transcript hashes with the raw predictions.

## Confirmed development result

The confirmed frozen output is stored under `outputs/rule-baseline/rule-baseline-v1.0-frozen/`. Human one-to-one review confirmed six matches and two false positives: micro precision `0.750`, recall `1.000`, F1 `0.857`, and macro F1 `0.833`. Among matched actions, owner-set accuracy was `6/6`; exact deadline accuracy was `2/3`. These are development diagnostics, not formal test results.

## Freeze record

The immutable file hashes are recorded in `configs/RULE_BASELINE_VERSION.json`. The rules must not change after the locked test run begins. Any necessary change requires a new version and a complete rerun of all affected experimental arms.
