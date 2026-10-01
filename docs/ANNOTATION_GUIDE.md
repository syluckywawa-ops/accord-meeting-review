# ActionAI Manual Annotation Guide v1

**Purpose:** Create human gold labels before seeing formal model outputs.  
**Applies to:** 3 development and 20 locked test transcripts in `data/data_manifest.csv`.  
**Annotator:** Lin Siyuan.  
**Rule:** When uncertain, record the candidate and explain the uncertainty. Never silently guess.

## 1. What to label

Label a statement when it creates identifiable work that should happen after that point in the meeting. It must express at least one of the following:

1. **Commitment:** a speaker accepts future work — “I will email the supplier.”
2. **Assignment:** someone gives future work to another person or role — “Ben, prepare the slides.”
3. **Accepted request:** a request is followed by clear acceptance — “Could you test it?” / “Yes, I will.”
4. **Group obligation:** the team clearly commits to an activity — “We need to finish the prototype by Friday.”

The final `task` must begin with a verb and describe only the agreed work, for example `email the supplier` or `finish the prototype`.

## 2. What not to label

Do not label:

- a decision without follow-up work: “We chose blue.”
- a rejected or unanswered suggestion: “Maybe someone could survey users.”
- completed work: “I emailed the supplier yesterday.”
- a vague ambition: “We want this product to be innovative.”
- procedural meeting talk: “Let us move to the next slide.”
- a physical movement or gesture;
- a task that exists only in the AMI summary but has no defensible transcript evidence.

## 3. Boundary rules

### 3.1 One action versus several

- Use one row when clauses are inseparable parts of one deliverable: “draft and send the single proposal.”
- Use separate rows when either task could be completed independently: “draft the budget and book the room.”
- Repeated mentions of the same task remain one action. Use the clearest evidence span and note additional evidence if useful.

### 3.2 Owner

- Use the normalised AMI role name when explicit: `Project Manager`, `Marketing Expert`, `Industrial Designer`, or `User Interface Designer`.
- When two or more roles are explicitly jointly responsible, list them in the CSV with `; ` between roles, for example `Industrial Designer; User Interface Designer`. The model output converts this to an `owners` array.
- A first-person commitment belongs to the current speaker: “I will check” means that speaker's role is the owner.
- “We” becomes `Team` only if the group clearly accepts collective responsibility.
- If no owner is explicit or unambiguous, use an empty cell, which will become an empty JSON `owners` array.
- Never select the most plausible owner based only on job role.

### 3.3 Deadline

- Copy the exact phrase into `deadline_text`, such as `by Friday`.
- Normalise only when the meeting date makes the date unambiguous.
- Use ISO `YYYY-MM-DD` for a date and `YYYY-MM-DDTHH:MM:SS` when an exact time is known.
- If no deadline is stated, leave both deadline fields empty.
- Expressions such as “soon” may be retained as deadline text but cannot be normalised.

### 3.4 Evidence

- Copy the shortest continuous transcript span that proves the task and, where possible, its owner and deadline.
- Preserve the source turn IDs exactly.
- If acceptance appears in a separate turn, include both turn IDs separated by `|` and the two exact quotes separated by ` || `. The number and order of IDs and quotes must match.
- Do not paraphrase `evidence_text`.

## 4. Explicitness labels

| Value | Use when |
|---|---|
| `explicit` | A direct assignment or explicit future obligation is stated |
| `self_commitment` | The speaker personally commits using “I will”, “I can”, or equivalent acceptance |
| `implicit_task` | Follow-up work is clearly agreed but phrased indirectly; explain why in `notes` |

`implicit_task` should be rare. It always requires careful review later.

## 5. Annotation procedure for each transcript

1. Start the timer and record `annotation_started_at`.
2. Read the complete transcript once without the AMI abstract summary.
3. On the second pass, enter every candidate action in `initial_labels.csv`.
4. Re-read the surrounding context for each candidate and apply the inclusion/exclusion rules.
5. Complete every required field and record any uncertainty in `notes`.
6. Stop the timer and record `annotation_finished_at` and `annotation_minutes`.
7. Set `label_status=initial_locked`. Do not open the official AMI `ACTIONS` summary before this point.
8. Compare the locked rows with the official summary and record every comparison in `adjudication_log.csv`.
9. If a gold row changes, preserve the original value and explain the reason in the adjudication log.
10. Set the final rows to `label_status=adjudicated_gold` only after the audit is complete.

## 6. Official-summary audit categories

| Category | Meaning |
|---|---|
| `match` | Manual and official references describe the same work |
| `manual_only` | Manual action has transcript evidence but no official counterpart |
| `official_only` | Official summary contains an action absent from initial manual labels |
| `scope_disagreement` | Both notice the same passage but split, merge, include, or exclude it differently |

The official summary does not automatically override the manual decision. Transcript evidence and this guide control the final gold label.

## 7. Quality check before locking a transcript

- [ ] Complete transcript read, not just keyword hits.
- [ ] Every action is future work rather than a decision or past event.
- [ ] Every task begins with a verb and contains a clear deliverable.
- [ ] Owner is explicit/self-committed or blank.
- [ ] Deadline is stated or blank; none is invented.
- [ ] Evidence text is verbatim and source IDs exist.
- [ ] Duplicate mentions are merged.
- [ ] Uncertainty is documented.
- [ ] Timing fields are complete.
- [ ] Official ACTIONS summary remained closed until `initial_locked`.

## 8. Synthetic calibration examples

These examples are invented and are not from a development or test transcript.

| Transcript excerpt | Label decision |
|---|---|
| PM: “Maya, please send the deck by Friday.” Maya: “Sure.” | Include; task `send the deck`; owner `Maya`; deadline `by Friday`; explicit |
| ME: “A survey might be useful.” | Exclude; unaccepted suggestion |
| UI: “I finished the mock-up yesterday.” | Exclude; completed work |
| ID: “I can test both materials.” | Include; owner is the current speaker; self-commitment |
| PM: “We chose plastic.” | Exclude unless a separate follow-up task is assigned |

## 9. Prohibited shortcuts

- Do not ask an LLM to create or rewrite the gold labels.
- Do not search the transcript using only action keywords instead of reading it.
- Do not inspect zero-shot, few-shot, or baseline outputs before initial labels are locked.
- Do not edit a label after scoring without preserving the original and logging the reason.
- Do not change the definition to improve an experimental arm's score.
