# ActionAI — Experiment Protocol v1

**Status:** Pre-registered working protocol. No formal model run may begin until every item in the final freeze gate is complete.  
**Protocol date:** 22 September 2026  
**Project owner:** Lin Siyuan  
**Course:** PE6201 Emerging AI Technologies — End-of-Course Individual Project

## 1. Research question and scope

**Research question:** How accurately and reliably can one structured large-language-model call extract action items, owners, and deadlines from AMI meeting transcripts, compared with a reproducible keyword-rule baseline?

**Primary user:** A project manager who must turn a completed internal meeting transcript into a reviewable follow-up list.

**Intended use:** Produce a draft action register for human verification immediately after a meeting.

**Non-use:** The system must not automatically assign work, notify employees, alter project records, or be used for performance assessment. It is not a source of truth and must not process confidential workplace transcripts in this project.

**Minimum viable product:** One transcript in, one model call, one validated JSON result out. Each extracted item contains a task, owner, deadline, supporting evidence, and a review flag.

The project does not attempt meeting summarisation, decision extraction, speech recognition, multi-call agents, fine-tuning, or production deployment.

## 2. Systems compared

The following three arms will be evaluated on the same locked test set and with the same output schema.

1. **Keyword-rule baseline.** Deterministic rules identify future commitments and assignments using modal/future verbs, assignment phrases, speaker self-commitments, and deadline expressions. The rules and keyword lists are frozen using development transcripts only.
2. **Zero-shot LLM.** One structured call, task definition and schema only, with no labelled examples.
3. **Few-shot LLM.** The same call and schema, plus two or three compact examples selected only from the development set. Examples must include at least one absent owner or deadline and one non-action sentence.

The zero-shot and few-shot arms must use the same provider, exact model ID, temperature, token limit, transcript formatting, parser, retry policy, and evaluation code. Temperature will be `0` where supported. A protocol amendment will freeze the exact model and price before any formal test call; the model may not be selected by comparing test-set results.

## 3. Data source and sampling plan

The project will use the **AMI Meeting Corpus manual annotations v1.6.2**, particularly scenario meetings that have both manual word-level transcripts and official abstractive summaries. AMI is public research data; the relevant manual annotations are distributed under CC BY 4.0. Only the supplied transcripts and metadata will be processed.

### 3.1 Fixed sample

- **Development set:** 3 complete scenario-meeting transcripts.
- **Locked test set:** all 20 complete meetings in the official scenario-only unseen evaluation partition.
- **Total:** 23 transcripts.
- Meetings from the same scenario series or team must not appear in both development and test sets.
- Each selected meeting must have a manual transcript and an official abstractive `ACTIONS` section.
- Development IDs: `ES2003a`, `ES2003b`, `ES2003c`.
- Test IDs: `ES2004a-d`, `ES2014a-d`, `IS1009a-d`, `TS3003a-d`, and `TS3007a-d`.
- The test IDs exactly follow the AMI scenario-only unseen evaluation partition and are never used for tuning.

### 3.2 Verified scale before manual annotation

The 20 test transcripts contain **121,820 transcribed word elements** and **28 non-NA official AMI action-summary sentences**. The three development transcripts contain 15,707 word elements and three non-NA official action-summary sentences. Entries whose official action section contains only `NA` or `*NA*` are counted as zero rather than as actions. These official sentences establish the reference scale but are not automatically treated as gold labels. The locked gold dataset contains **51 adjudicated action items: 6 in development and 45 in test**. This differs from the official-sentence count because the protocol's operational definition can split, merge, include, or exclude an official summary sentence with a documented reason. No meeting will be added or removed in response to model performance.

### 3.3 Leakage controls

- Development transcripts may be used to design rules, prompts, few-shot examples, and parsers.
- Test transcripts and their official summaries may not be inspected for prompt or rule tuning after the test set is frozen.
- No test transcript, paraphrase, official action summary, or gold label may appear in the few-shot prompt.
- All formal model outputs are stored before scoring begins.
- A meeting series is the splitting unit; individual utterances are never randomly split across sets.

## 4. Gold-label construction

Lin Siyuan will manually label every selected transcript before any formal model output is viewed.

### 4.1 Definition of an action item

An action item is a future-oriented commitment, request, or assignment that creates follow-up work after the relevant point in the meeting. It may be assigned to a named person, a role, the current speaker, or nobody explicitly identified.

Exclude:

- decisions with no follow-up work;
- ideas, options, or suggestions that nobody accepts;
- statements about work already completed;
- general goals with no actionable step;
- ordinary meeting-management speech such as “let us move on”;
- physical gestures labelled “individual actions” in some AMI documentation.

### 4.2 Gold schema

Each gold record must contain:

| Field | Rule |
|---|---|
| `transcript_id` | AMI meeting identifier |
| `action_id` | Stable identifier unique within the transcript |
| `task` | Concise verb-led description of the required work |
| `owner` | CSV storage: one or more explicit roles separated by `;`, unambiguous self-commitment speaker, `Team`, or blank |
| `deadline_text` | Exact stated deadline phrase, or `null` |
| `deadline_normalized` | ISO date/time where determinable from meeting metadata, otherwise `null` |
| `evidence_text` | Minimal verbatim transcript span supporting the label |
| `evidence_ids` | Source utterance/word identifiers |
| `explicitness` | `explicit`, `self_commitment`, or `implicit_task` |
| `notes` | Ambiguity or adjudication rationale |

An owner may be inferred only for an unambiguous self-commitment by the current speaker. Joint owners are allowed only when every role is explicitly assigned and are converted from the CSV's semicolon-separated representation into a JSON `owners` array. A deadline may never be invented. Relative dates are preserved in `deadline_text`; normalisation requires a known meeting date.

### 4.3 Independent audit using AMI summaries

Manual labels are timestamped and locked first. Only then are they compared with the official AMI abstractive `ACTIONS` section. Each difference is recorded as `match`, `manual_only`, `official_only`, or `scope_disagreement`. The final gold label may be amended only through a documented adjudication entry giving the original label, external reference, final decision, and reason. Official summaries are an audit source, not prompt content and not an automatic gold standard.

## 5. Output contract and abstention

The model returns a JSON object with a top-level `action_items` array. Each item contains:

```json
{
  "task": "string",
  "owners": ["Project Manager"],
  "deadline_text": "string or null",
  "deadline_normalized": "ISO string or null",
  "evidence_text": "string",
  "needs_review": true,
  "review_reason": "string or null"
}
```

`needs_review` must be true when evidence is missing, the task is only implicit, owner or deadline attribution is ambiguous, commitments conflict, the transcript is truncated, or validation fails. The pipeline must reject invalid JSON, missing required fields, unsupported evidence, and silent transcript truncation. It may retry once only for syntax/schema repair; the retry and its token cost must be logged.

## 6. Matching and scoring rules

### 6.1 Action matching

Predicted and gold actions are matched one-to-one within the same transcript. A task match is accepted when both describe the same underlying work and deliverable, even if voice, word order, or close synonyms differ. For example, “Ben to send the slides” and “send the deck to Ben” match on the task if the meeting context establishes that slides and deck refer to the same deliverable; owner scoring is performed separately.

Rules:

- One prediction cannot match more than one gold item, and vice versa.
- If one prediction merges two independent gold tasks, it can match only one; the other is a false negative.
- If multiple predictions split or duplicate one gold task, only the best-supported prediction matches; the rest are false positives.
- A more general prediction matches only when it preserves the central action and deliverable.
- Owner or deadline disagreement does not turn a correct task into a task miss; those fields receive separate scores.
- Borderline matches are adjudicated without revealing which experimental arm produced them. The reason is logged.

### 6.2 Primary metric

**Micro-averaged action-item F1** across all locked test transcripts is the primary metric. True positives are one-to-one task matches; unmatched predictions are false positives; unmatched gold items are false negatives.

### 6.3 Secondary metrics

- action precision and recall;
- macro F1 across transcripts;
- owner-set exact/normalised accuracy among matched actions with at least one gold owner;
- deadline accuracy among matched actions with an explicit gold deadline;
- hallucinated-owner and hallucinated-deadline rates when the gold field is null;
- valid-JSON rate and evidence-support rate;
- duplicate-action rate;
- `needs_review`/abstention rate and error rate inside versus outside flagged items;
- input tokens, output tokens, total cost, latency, and retry rate per transcript;
- descriptive human review time in minutes per 1,000 input tokens for five pre-declared test transcripts.

The five-transcript timing exercise is descriptive only. It will not support a causal claim that AI reduces review time, because one evaluator and repeated exposure create learning and memory effects.

## 7. Success criteria fixed before testing

The few-shot system will be considered practically promising only if all primary gates are met:

1. micro action F1 is at least **0.75**;
2. micro action F1 exceeds the keyword baseline by at least **0.10 absolute**;
3. action precision is at least **0.80**;
4. valid structured output rate is at least **95%**;
5. hallucinated-deadline rate is at most **5%**;
6. every output contains traceable transcript evidence or is flagged for review.

Failure to meet a threshold will be reported, not hidden or repaired by changing the test set. Zero-shot versus few-shot improvement is an experimental result, not a required success condition.

## 8. Cost and long-context protocol

Before formal runs, the pipeline will count model-specific tokens for every transcript and both prompt variants. It will calculate expected input/output cost using the provider's documented price and compare the full experiment with the **USD 10** course-key constraint.

For each call, log:

- exact provider and model ID;
- prompt version and hash;
- input/output token counts;
- estimated and actual cost where available;
- latency, HTTP status, retry count, and error message;
- context-window utilisation and any rejected transcript.

Transcripts must never be silently truncated. If a complete transcript exceeds the frozen model context or budget, the run is marked `not_processed`, reported as a coverage failure, and not replaced selectively. Few-shot overhead will be reported separately.

## 9. Risks and safeguards

| Risk | Concrete safeguard and measured signal |
|---|---|
| Missed commitments create silent false negatives | Recall is a headline metric; five transcripts receive manual error review; output is always labelled a draft |
| Invented owner or deadline | Nullable fields, evidence requirement, review flag, and explicit hallucination rates |
| Ambiguous or conflicting commitments | `needs_review` plus reason; no automatic downstream action |
| Transcript text contains prompt-like instructions | System prompt treats transcript as untrusted quoted data; injection test cases are included in development checks |
| Long transcripts exceed context or budget | Preflight token count, hard budget check, no silent truncation, coverage reported |
| Sensitive meeting content | Only public AMI data; no real employer/customer transcript in the repository or demo |
| Evaluation leakage | Series-level split, gold labels locked before test outputs, development-only tuning |
| Reproducibility failure | Pinned dependencies, deterministic baseline, saved configs/raw outputs, one-command evaluation |

## 10. Reproducibility and repository requirements

The final repository must run on a clean environment and include:

- a README with problem, setup, data licence/source, commands, expected runtime, cost warning, and limitations;
- a data manifest containing exact meeting IDs, split, word/token counts, and annotation availability;
- annotation instructions, initial labels, adjudication log, and final gold labels;
- baseline, zero-shot, few-shot, validation, scoring, cost, and plotting code;
- versioned prompts and JSON schema;
- raw outputs with secrets and personal data removed;
- pinned dependencies and an `.env.example` without keys;
- tests for schema validation, matching edge cases, no-silent-truncation, and budget calculation;
- generated metrics tables and figures used in the report and video.

## 11. Formal freeze gate

Formal test calls are prohibited until all boxes are complete:

- [x] Exact meeting IDs recorded in `data/data_manifest.csv`.
- [ ] Development/test split checked for meeting-series and participant leakage.
- [ ] All manual labels completed and timestamped before model inspection.
- [ ] Official-summary audit and adjudication log completed.
- [ ] Rule baseline, zero-shot prompt, few-shot examples, schema, and matching tests frozen.
- [ ] Exact provider/model ID, temperature, context limit, and prices recorded.
- [ ] Per-transcript token counts and total worst-case cost calculated and within budget.
- [ ] Five timed-review transcripts declared.
- [ ] Dry run passes on development data, including malformed JSON and prompt-injection checks.
- [ ] User can explain the pipeline, labels, metrics, and known limitations without relying on an assistant.

Any post-freeze change must be versioned, justified, and followed by a complete rerun of all affected arms. Test results may never be deleted because they are unfavourable.

## 12. Planned analysis and reporting

The report will present: quantified workflow pain; nearest existing alternative and gap; data and licence; experimental design; primary/secondary results; cost per transcript and projected throughput under USD 10; representative success and failure cases; trade-offs among rules, zero-shot, and few-shot; risk controls; limitations; and a narrow deployment recommendation. The written analysis will remain within **1,200 words**. The video will demonstrate one complete input-to-output flow and one failure/abstention case using reproducible repository commands. The final submission must also include the official self-appraisal cover document, completed from traceable evidence of the student's own decisions, implementation, checks, learning, and use of assistance.

## 13. Decisions still to be frozen in v1.1

The following are deliberately unresolved at this stage and must be settled using development data or provider documentation, never test performance:

- exact provider and model ID;
- exact rule dictionary and parsing implementation;
- exact two or three few-shot examples;
- exact five transcripts used for descriptive review timing.
