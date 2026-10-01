# Accord: product and architecture

## Who it is for and what problem it addresses

The intended user is a project manager or meeting owner who already has a transcript and needs to prepare a follow-up list. A transcript is not itself a reliable task register: requests, decisions, suggestions, and repeated discussion can look similar. Accord helps the reviewer locate candidate follow-up work, check it against exact source turns, and export only the decisions they have approved. It does not independently assign tasks to colleagues or update an organisation's systems.

The project has **two linked but distinct outcomes**. ActionAI is the frozen three-method evaluation on 23 AMI meetings; it tests whether structured extraction is accurate and reliable enough. Accord is the working review interface informed by that result. Accord's new-upload adapters were built later and do **not** inherit the AMI test scores.

## Inputs and outputs

| Path | Input | Output | Important boundary |
|---|---|---|---|
| Frozen experiment | 23 public AMI transcripts with fixed development/test split; 51 human gold actions | Saved rule, zero-shot, and few-shot predictions; validation status; human-adjudicated metrics | The 20 test meetings were not used to tune the systems. Invalid model outputs receive no task credit. |
| Saved-example review | One included AMI meeting, one of the three saved prediction methods | Evidence-linked candidate list, reviewer decisions, audited approved JSON/CSV | Reading saved outputs makes no provider call. Approval and full-transcript scan are required for export. |
| New-meeting review | Pasted transcript or UTF-8 TXT, text PDF, or DOCX, with editable preview | Local-rule drafts or optional Live AI drafts, followed by human review and export | This is a product trial, not a measured benchmark. Live AI sends text to OpenRouter and may cost money. |

The task output records a task, owner list, optional deadline text and normalised date, exact supporting quote and turn IDs, and a review flag. Completion checkboxes are separate post-approval task-tracking metadata, not an accuracy claim or an automatic assignment.

## High-level architecture

```text
Public AMI source -> prepare_ami.py -> 23 transcript + turn-metadata files
                                      -> manual gold labels (locked)
                                      -> [frozen rule | zero-shot LLM | few-shot LLM]
                                      -> schema/evidence validator -> saved predictions
                                      -> documented human one-to-one match review
                                      -> final_comparison.json

Pasted text / TXT / text PDF / DOCX
             -> bounded local parser -> editable transcript preview
             -> [simple local rules | optional OpenRouter Live AI]
             -> product evidence validator -> Accord browser review
             -> accept / edit / reject / add + full-transcript check
             -> approved JSON or CSV + audit history + completion state
```

The browser is `web/review.html`. `scripts/run_review_workspace.py` serves the local HTTP API and saved example catalog. `actionai/document_import.py` parses documents; `actionai/imported_meetings.py` converts imports to evidence-addressable turns and runs product-only extraction; `actionai/output_validation.py` checks structure and source evidence; `actionai/review_workspace.py` manages decisions, audit history, advisory v1.1 review hints, and export gates. The hints never change the frozen predictions or make automatic approval decisions. `actionai/rule_baseline.py`, `actionai/llm_pipeline.py`, `actionai/prompts.py`, and `actionai/evaluation.py` implement the frozen research workflow, with versioned assets in `configs/`, `prompts/`, and `schemas/`. The executable experiment and data-preparation entry points are documented in `README.md` and `scripts/`.

## Target versus reached

| Measure | Pre-declared threshold | Locked few-shot test result |
|---|---:|---:|
| Action-item micro F1 | >= 0.75 | 0.505 |
| Improvement over rule baseline | >= 0.10 absolute | +0.292 |
| Action precision | >= 0.80 | 0.463 |
| Valid structured output | >= 95% of meetings | 85% (17/20) |
| Hallucinated deadline | <= 5% | One unsupported deadline among seven eligible matched actions without a gold deadline; threshold not met |
| Traceable evidence | Exact transcript evidence, or review flag | Validator checks quoted evidence; 3/20 outputs still failed validation after one repair |

The comparison shows a useful improvement over the reproducible keyword baseline, but not a production-ready extractor. The human review gate is a safety and workflow choice, **not proof** that review is faster than writing a list manually. Five meetings averaged 60.6 net review minutes each; the corrected date and de-identified observations are in `data/review_timing_public.md`. This exercise lacked a manual-only control. New uploads, especially live AI, need their own evaluation before any accuracy or time-saving claim.

## Known rough edges and operating limits

The local server uses visitor cookies rather than user accounts and is not a secured multi-user deployment. Text PDFs work, but scanned PDFs need OCR; legacy DOC and audio are unsupported. The parser's editable preview helps correct lost speaker structure, but the reviewer still owns that correction. The local-rule import adapter catches simple self-commitments and can miss cross-speaker assignments. Live AI has a mocked adapter test but has not been verified with a paid production call; it should not be described as a validated service. No public hosted website is promised by this repository: the code runs locally using the README commands.

The data and measurement rationale are in `docs/DATA_EXPLAINER.md` and `docs/EVALS_EXPLAINER.md`.
