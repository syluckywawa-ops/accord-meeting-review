# Data explainer: what is checked in and why

## Origin, licence, and scope

The study uses the public **AMI Meeting Corpus manual annotations v1.6.2**. The source and its download checksum are listed in `data/SOURCE.md`. The relevant public transcription and annotation material is distributed under **CC BY 4.0**; attribution to the AMI Meeting Corpus must be retained. No employer or banking-customer recordings are used. The original AMI archive and extracted NXT source directory are not checked in because they are large and can be downloaded and verified with `scripts/download_ami.py`.

The repository includes the actual **derived input data used for this project**: 23 readable transcripts in `data/derived/transcripts/`, their 23 turn-level JSON files in `data/derived/metadata/`, and `data/derived/preparation_summary.json`. `scripts/prepare_ami.py` regenerates these from the checksum-pinned source. Each turn has a stable ID, speaker role, text, and timing so that a claimed action can be checked against the conversation. These files are public-corpus derivatives, not private uploads. Imported user documents and review sessions are excluded from the repository.

One additional public AMI transcript, ES2002a, and its metadata are stored separately in `data/exploratory_v11/` for a post-experiment product review. Its student's completed review form is preserved there unchanged. ES2002a is **not** in the fixed 23-meeting manifest or the 20-meeting test denominator.

## Sampling and labels

`data/data_manifest.csv` fixes 3 development meetings (`ES2003a–c`) and 20 test meetings from the unseen scenario partition. The series, not individual utterances, is the split unit. The set contains **51 manually adjudicated action items**: 6 development and 45 test. `IS1009b` and `IS1009d` have zero gold actions; an empty label list is meaningful, not missing data. The manifest records exact IDs, split, word counts, annotation availability, and selection status.

An action is future follow-up work, not a design preference, a completed task, or ordinary in-meeting activity. Gold rows in `data/labels/final_gold_labels.csv` contain a task, owner, deadline fields, exact evidence, source turn IDs, explicitness, and adjudication notes. `docs/ANNOTATION_GUIDE.md` defines the label rules. `data/labels/initial_labels.csv`, `data/labels/annotation_progress.csv`, and `data/labels/adjudication_log.csv` show the development and audit trail. `data/labels/LABEL_VERSION.json` records the freeze time and hashes. The official AMI action summaries were an **audit reference after initial labelling**, not an automatic gold set or prompt examples.

## Reproducibility and limitations

Use `python3 scripts/validate_labels.py --labels data/labels/final_gold_labels.csv --manifest data/data_manifest.csv --metadata-dir data/derived/metadata` from the repository root to check labels against the included turns. Unit tests and the local example viewer need no AMI download because the relevant derived files are checked in. A separate source download and preparation step lets an examiner independently reproduce the derivation.

This is a small, selected **research benchmark**, not a representative sample of banking or current workplace meetings. AMI's role-play design, transcription style, and meetings from the 2000s may not transfer to new organisations or languages. A single human gold set can omit plausible actions; potential omissions found after model runs remain documented but are **not** silently inserted into the fixed scoring set. The repository's new-upload example PDF is fictional and is a smoke test, not an extra labelled benchmark. The five-meeting manual review timing summary names Lin Siyuan as reviewer and documents the date correction in `data/review_timing_public.md`.
