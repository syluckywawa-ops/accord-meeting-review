# Accord v1.1: one outside-sample AMI review

**Date:** 2 October 2026. **Reviewer:** Codex assistant, acting as a critical reviewer; **not** an independent human annotator. This check is separate from the locked 23-meeting ActionAI sample and does not change its labels, predictions, F1, or preregistered conclusions.

## Source and method

The source is AMI manual transcript **ES2002a** (13 December 2004), 207 merged turns and 3,105 transcribed word elements. It was not one of the 23 meetings in `data/data_manifest.csv`. The full transcript and turn metadata are in `data/exploratory_v11/`; the original source and CC BY 4.0 attribution are described in `data/SOURCE.md`. I read all 207 turns and made an initial action judgement **before** opening the product's candidate list. I did not consult AMI's abstractive action summary or the project's frozen labels for this meeting. This is one purposively selected meeting, not a random or representative sample.

I then ran the product's free, deterministic **Local rules** path on the whole transcript, inspected each draft and its source turn, and performed the final manual omission scan. `scripts/check_v11_real_meeting.py` replays the decisions and checks that the reviewed list passes the same evidence and export gates. No Live AI call, paid API, blinded second reviewer, or review-time measurement was involved.

## Candidate decisions

| Draft | Source turn | AI-assisted review decision | Reason |
|---|---|---|---|
| “go” | `ES2002a-T0019` | Reject | The marketing expert volunteers to go first in the animal-drawing exercise **during** the meeting. Not a follow-up deliverable. The short-quote advisory warning appeared. |
| “just draw a different kind of dog” | `ES2002a-T0052` | Reject | The project manager is drawing in the same icebreaker. Not a future project task. No v1.1 warning appeared. |
| “just check we've nothing else” | `ES2002a-T0149` | Reject | The project manager is checking the agenda while wrapping up the current meeting. Not an assigned post-meeting task. No v1.1 warning appeared. |

The possible-duplicate hint did not trigger: these three drafts are unrelated, so this case gives **no** evidence about that hint's effectiveness. The context-poor-evidence hint surfaced one of the three unsuitable drafts; it did **not** identify all three false positives.

## Missed-action scan

At `ES2002a-T0176`, the project manager says the next meeting is in thirty minutes and allocates interim work to the industrial designer and user interface designer. The marketing expert's requirements work continues into `ES2002a-T0178`. I therefore added three distinct, evidence-linked actions:

| Manually added action | Owner | Evidence | Deadline handling |
|---|---|---|---|
| Develop the remote control's working design | Industrial Designer | `T0176` | Before the next meeting, said to be in thirty minutes |
| Work out the remote control's technical functions | User Interface Designer | `T0176` | Same |
| Identify the remote control's requirements | Marketing Expert | `T0176`, `T0178` | Same |

These assignments are less specific than a finished deliverable and the speakers do not each repeat a verbal acceptance. The wording nevertheless presents role-specific work to be done *between now and the next meeting*, so I retained them as actionable with this uncertainty disclosed. I did **not** convert the earlier remote-control ideas, design preferences, or tentative questions into additional assignments. I left the machine-readable deadline null: the transcript provides a relative interval but not a reliable absolute local date/time for export.

## Result and limits

The local-rule extraction yielded **3 drafts**, all rejected after source review; the full-transcript scan added **3 missed actions**. Under these single-reviewer judgements, that is 0 matched, 3 unmatched, and 3 missed actions for this *one* meeting. The reviewed register contains 3 evidence-supported actions, and the export gate opens only after all three drafts are resolved and the scan is confirmed. These numbers are **not** an update to the formal three-arm test: the route is the product's Local rules importer, the meeting was chosen for a small check, and the judgements were made by the assistant rather than an independent human.

This case exposes the limitation clearly: v1.1's cues can draw attention to some questionable evidence, but they do not rescue omissions or replace a complete human read. The result supports presenting Accord as a **human-reviewed drafting and audit workflow**, not as a reliable automatic task extractor or a proven time-saving system. For a defensible improvement claim, use multiple fresh representative meetings, at least one independent human adjudicator, a frozen match policy, and assisted-versus-manual-only timing and final-list comparisons.

Lin Siyuan subsequently submitted a separate source-based review of all 207 turns. It agreed on rejecting the three local-rule drafts and retaining three interim work assignments. The unchanged student form and the checked, report-safe interpretation are documented in [the student-review note](PRODUCT_V1_1_STUDENT_REVIEW.md). The review was not blind to the earlier assistant analysis and was not timed.

## Report-ready wording

“I also checked the product workflow on ES2002a, an AMI meeting outside the frozen sample. Reading the full transcript first, I identified three role-specific tasks set for the next meeting. The Local rules importer instead drafted three in-meeting activities and missed those tasks. Accord's evidence warning drew attention to one unsuitable draft, while the required omission scan made it possible to add the three supported actions before export. This small, assistant-reviewed check is useful for finding rough edges in the workflow, but it is neither an independent human evaluation nor proof of higher accuracy or lower review time.”
