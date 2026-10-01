# Accord

Turn meeting conversations into verified action items.

Accord is the product name of the ActionAI research project. Historical experiment files, frozen prompts, gold labels, and scores retain their original names and are unchanged by this interface rebrand.

ActionAI is a PE6201 individual project that evaluates rule-based, zero-shot, and few-shot extraction. Those results inform Accord, an evidence-grounded human review workspace. The system drafts action items, owners, and deadlines from meeting transcripts, validates output, and requires human approval before export. New uploads use a separate local-rule or optional Live AI product route; their accuracy is not established by the frozen AMI experiment.

## Current status

The locked three-arm formal experiment and human review are complete. On 20 unseen test meetings containing 45 fixed gold actions, the rule baseline achieved micro F1 0.213, zero-shot achieved 0.403, and few-shot achieved 0.505. Few-shot was the strongest arm, but it did not meet the pre-registered production gates; ActionAI is therefore recommended only as a human-reviewed drafting tool. See:

- `EXPERIMENT_PROTOCOL_v1.md` for the pre-registered design;
- `docs/ANNOTATION_GUIDE.md` for gold-label rules;
- `data/data_manifest.csv` for the locked 3-development/20-test sample;
- `data/SOURCE.md` for provenance, licence, and checksum.
- `data/review_timing_public.md` for the named reviewer's five-meeting timing observations and date-correction history;
- `outputs/final-analysis/final_comparison.json` for the consolidated final metrics;
- The final written report and recorded presentation are separate submission materials and are not part of this source snapshot.

The final deliverables are a clear problem statement record, a business/technical trade-off analysis, a working GitHub implementation, a recorded working demonstration, and the official self-appraisal cover document. The instructor's later email asks for a report around 1,200 words (within roughly 10–15%), and a 2–8 minute demo with both the student's face and screen visible.

For a guided repository tour, start with [product and architecture](docs/PRODUCT_ARCHITECTURE.md), [data explainer](docs/DATA_EXPLAINER.md), and [evaluation explainer](docs/EVALS_EXPLAINER.md). These separate the frozen scientific result from the newer, not-yet-benchmarked product import path.

Accord v1.1 adds advisory duplicate/evidence review cues and a more visible missed-action scan. The separate fictional workflow check and its strict limitations are in [the v1.1 trial note](docs/PRODUCT_V1_1_EXPLORATORY_TRIAL.md). The locked action F1 values above did not change.

A separate [one-meeting real-transcript check](docs/PRODUCT_V1_1_REAL_MEETING_CHECK.md) uses AMI ES2002a outside the formal 23-meeting sample. It is an AI-assisted manual review of the product's Local rules import path, not a new independent human evaluation. The full source and turn metadata are in `data/exploratory_v11/`, and the decision replay is `scripts/check_v11_real_meeting.py`.
Lin Siyuan later checked all 207 source turns and submitted a separate [student review](docs/PRODUCT_V1_1_STUDENT_REVIEW.md); the completed form is preserved unchanged with the exploratory data. This source-based agreement is not blinded inter-annotator validation, and its approximate review time was not measured.

## Data

The project uses the AMI Meeting Corpus manual annotations v1.6.2. The 23 derived transcripts and their turn-level metadata used in this project are included in `data/derived/`, alongside the fixed labels and manifest, so the included examples and evidence can be inspected immediately. The much larger original AMI archive and extracted source directory are not included. To independently regenerate the derived files, download the official archive listed in `data/SOURCE.md`; the downloader verifies its SHA-256 checksum.

No AMI meeting audio or video files are required for the dataset pipeline. This is separate from the course requirement to submit a recorded project demonstration. No confidential workplace data is used.

## Quick local demonstration

From a clean copy of this repository:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_review_workspace.py --port 8503
```

Open `http://127.0.0.1:8503`. Pick a saved AMI meeting to inspect the frozen outputs, or import `output/pdf/Accord_Test_Meeting.pdf` below the Meeting selector and choose **Local rules**. The fictional PDF route needs no API key or network call. Its expected and missed actions are documented in `docs/PDF_IMPORT_TEST.md`. The saved AMI examples use the checked-in derived metadata and make no new model calls. Stop the local server with Ctrl+C. These are research/demo workflows, not a publicly deployed service.

## Regenerate readable transcripts from the source archive (optional)

From the repository root, install dependencies if not already done, then download and prepare the public AMI source. The preparation command writes the same paths as the included derived data, so run it in a fresh copy if you wish to preserve the submitted snapshot for comparison:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/download_ami.py
.venv/bin/python scripts/prepare_ami.py \
  --source data_raw/ami_public_manual_1.6.2 \
  --manifest data/data_manifest.csv \
  --output data/derived
```

This produces readable transcript files with stable evidence IDs in `data/derived/transcripts/` and structured metadata in `data/derived/metadata/`. It intentionally does not export official AMI action summaries, protecting the manual-label-first protocol.

## Run current tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Open the review workspace

Run from the project root, using the included derived transcripts and metadata:

```bash
.venv/bin/python scripts/run_review_workspace.py --port 8503
```

Open `http://127.0.0.1:8503`. The AMI sample viewer uses frozen test outputs for all three methods; loading these makes no API calls. Candidates can be accepted, edited, rejected or reopened, and missed actions can be added with exact transcript evidence. Export remains blocked until every candidate has a decision and the reviewer confirms the full-transcript scan. An invalid extraction starts a manual reconstruction workflow. The private raw provider logs are not needed to run the sample viewer.

The import panel accepts pasted text, UTF-8 TXT, text-based PDF and DOCX files up to 8 MB. Inspect and correct the editable text preview before extraction. Use `Name: speech` on separate lines to preserve speaker attribution. Scanned PDF needs external OCR; legacy DOC and audio are not currently supported. Imported transcripts run local extraction without network access, or live AI when `OPENROUTER_API_KEY` is configured on the server. Keys are never entered in the webpage. Imported live AI sends the transcript to OpenRouter and incurs charges; the interface displays this before submission. The product import adapters are separate from the frozen experimental methods and their reported scores. See `docs/REVIEW_WORKSPACE_DEPLOYMENT.md` for capabilities and outstanding live/deployment verification.

Review records and original candidates are saved separately in `outputs/review-workspace/`, with an audit history. These demo edits never update gold labels or formal scores. JSON exports include the history; CSV exports contain the approved list. Random cookies isolate browser sessions, but are not login authentication. The local server is a demonstration service. Public hosting still requires hardening and deployment setup; a localhost address is not a teacher-accessible URL.

## Validate manual labels

During annotation, run:

```bash
python3 scripts/validate_labels.py \
  --labels data/labels/initial_labels.csv \
  --manifest data/data_manifest.csv \
  --metadata-dir data/derived/metadata
```

The locked experiment labels are in `data/labels/final_gold_labels.csv`. They contain 51 adjudicated actions across 21 meetings; `IS1009b` and `IS1009d` are documented zero-action meetings. Validate the locked labels with:

```bash
python3 scripts/validate_labels.py \
  --labels data/labels/final_gold_labels.csv \
  --manifest data/data_manifest.csv \
  --metadata-dir data/derived/metadata
```

`data/labels/LABEL_VERSION.json` records the locked workbook and CSV SHA-256 hashes. Do not edit the locked label files after beginning development or test runs; create a new explicit version if a correction becomes necessary.

Before the formal experiment, add `--require-all-locked`. The validator checks schema, IDs, evidence against source turns, owner/deadline conventions, timing fields, duplicates, and dataset coverage.

## Reproducibility warning

The formal test outputs are frozen. Do not rerun or replace them selectively. Any changed model, prompt, rule, schema, label version, or evaluation policy must receive a new version and a complete rerun of every affected arm.

## Develop the keyword-rule baseline

Run the deterministic baseline only on the declared development split:

```bash
python3 scripts/run_rule_baseline.py --split development
```

Prepare the required human semantic-match review sheet:

```bash
python3 scripts/prepare_match_review.py \
  --predictions outputs/rule-baseline/rule-baseline-v1.0-dev/development.json \
  --output outputs/rule-baseline/rule-baseline-v1.0-dev/development_match_review.csv
```

The runner refuses a test-set execution without an explicit safety switch. Do not use that switch until all freeze-gate items are complete and the baseline version is frozen.

## Set up the LLM experiment

Create the isolated environment and install the pinned dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run the token and budget preflight without making an API call:

```bash
.venv/bin/python scripts/preflight_budget.py
```

Preview a development call without spending credit:

```bash
.venv/bin/python scripts/run_llm_experiment.py \
  --condition zero_shot \
  --split development \
  --meeting-id ES2003a
```

The API key must be supplied only through the `OPENROUTER_API_KEY` environment variable. Never paste it into source code, a notebook cell, an output file, or the repository. Development execution additionally requires `--execute`. Test execution is refused while the LLM configuration remains in development status.

For the first paid development check, use a hidden terminal prompt rather than placing the key in a command or file:

```bash
.venv/bin/python scripts/run_llm_experiment.py \
  --condition zero_shot \
  --split development \
  --meeting-id ES2003a \
  --execute \
  --prompt-for-key
```
