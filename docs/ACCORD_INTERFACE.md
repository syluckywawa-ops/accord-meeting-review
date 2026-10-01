# Accord interface

Accord is the product-facing name of the ActionAI research prototype.

Tagline: **Turn meeting conversations into verified action items.**

The rebrand changes the browser title, product wordmark, workspace copy, and reviewed-export filenames. It does not rename Python modules, change the frozen experiment, modify gold labels, or alter reported metrics.

## Interface revision, 30 September 2026

- One visual stylesheet replaces four accumulated style layers.
- Warm white and sage surfaces, a serif wordmark and heading, and restrained vector decoration establish the product identity without external asset downloads.
- Meeting and method selection sit above the source and draft, rather than in the sidebar.
- Pending, approved, and rejected counts reflect the saved review state.
- All / Pending / Approved / Rejected filters work on the current review decisions.
- Rejected actions show Reopen rather than redundant Accept / Edit / Reject controls. Pending actions do not show Reopen.
- Search includes speaker labels in addition to phrases and evidence IDs.
- Exports remain gated on reviewing every candidate and confirming the full-transcript scan, including actions hidden by filters.
- PDF, DOCX, and TXT parsing continues to use the existing local document parser.
- Approved actions are numbered and have reversible completion checkboxes, a Done / To do indicator, and a completed-total summary. Completed task text is struck through.
- Completion is saved per visitor and meeting, with timestamps and audit entries. It is distinct from human approval and does not reset the full-transcript scan. Editing, reopening, or rejecting an action resets its completion.
- Reviewed JSON keeps the validated extraction fields unchanged and adds a separate task_tracking list. Reviewed CSV adds completed and completed_at columns. Neither changes frozen experiment exports.

## Verification

Browser checks covered rejection, filtered results, reopening, evidence highlighting, blocked export before review, importing a fictional meeting with local rules, editing the deadline phrase, approval, and enabling export after full-transcript confirmation. Backend and markup regression tests are run separately. Product review edits remain visitor-specific and do not feed into formal scores.

Local extraction still leaves deadline fields for manual confirmation. A deadline phrase appearing in the task is not proof that the deadline field was extracted. The interface remains a research prototype, not an independently validated production service.

Checklist verification used the fictional Accord interface check meeting: check, refresh and reopen, and uncheck all passed in the browser. Computed task decoration was line-through when completed. Export stayed enabled after completion changes, while approval and scan requirements remained enforced. All 52 unit tests passed, including legacy-state defaults, audit history, strict boolean inputs, and completion reset on edits or revoked approval.

## Guided demonstration refinement, 1 October 2026

- The first selector group now names three purposeful research demonstrations: design coordination (`TS3003c`), a method-dependent validation case (`ES2004d`, where few-shot requires manual reconstruction), and final handoff (`TS3007d`). The other 17 held-out meetings remain available in a separate research group; personal imports remain separate again.
- A short context strip identifies saved research output versus a new, unbenchmarked import. It explains the reviewer's task and visibly calls out validation failure. Saved examples make no new API request; the import route is not assigned the formal test F1.
- The top bar and introductory section are shorter, bringing the transcript and action draft into the initial viewport sooner. The underlying decisions, export gate, scores and frozen files are unchanged.
- These changes were checked in the local browser and the interface regressions are included in the 53-test suite. They improve demo comprehension, not extraction accuracy.

## Advisory review refinement, 2 October 2026

Accord v1.1 adds non-blocking possible-duplicate and thin-evidence messages to current model drafts, plus a clearer full-transcript omission reminder. The warning logic is in `actionai/review_workspace.py` and does not modify the saved predictions, frozen evaluation, review decisions, or exported task fields. The separate fictional seven-turn check, its expected reviewer corrections, and its limitations are documented in `docs/PRODUCT_V1_1_EXPLORATORY_TRIAL.md`. The local browser workflow and 55 unit tests passed; no claim of improved accuracy or reduced manual time follows from this small check.
