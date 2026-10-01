# Review workspace delivery

The browser interface supports frozen rule, zero-shot and few-shot outputs, pasted transcripts, UTF-8 TXT, text-based PDF and DOCX imports, transcript search, evidence navigation, acceptance, editing, rejection, manual additions, audit history, and gated JSON/CSV exports. Documents produce editable previews before extraction. Imported meetings support arbitrary participant names and use product-specific validation without changing frozen experiment assets.

Local extraction uses a new, deliberately simple rule adapter for English and Chinese self-commitments. It is not the frozen AMI baseline, and has no measured accuracy claim. Live AI uses a separate product prompt and schema that permit arbitrary names, with the existing transport and one-repair policy. It likewise does not inherit the formal experiment's F1. Live AI requires the pinned dependencies and `OPENROUTER_API_KEY` in the server environment; the interface disables it when the key is absent. No new paid API call has yet been used to verify this product path. Extracted text is limited to 150,000 characters, documents to 8 MB and PDF to 100 pages. Scans require external OCR. Audio transcription is not implemented.

Each browser receives a random visitor cookie. Saved review files are separated by visitor, method and meeting. The service runs locally by default. To prepare a hosted instance, use `python3 scripts/run_review_workspace.py --host 0.0.0.0 --port 8501` inside the hosting environment only.

Public deployment requires the code, frozen prediction JSON files, derived meeting metadata and `web/review.html`. Raw provider logs are optional private audit artifacts: when absent, their per-meeting token and validation-detail display may be unavailable, but review remains functional. Do not upload API keys, personal timing workbooks, private files or local demonstration review sessions. Attribute AMI and its CC BY 4.0 licence. A clean checkout regenerates derived data with `scripts/download_ami.py` (checksum verified) and `scripts/prepare_ami.py`, as documented in the README.

Before sharing the final URL, verify HTTPS, the service's uptime, persistence policy, independent sessions in two browsers, invalid-run reconstruction, and downloads. Visitor data may be temporary if the host has no persistent storage; disclose that in the interface. The current standard-library server is a demonstration service, not a production deployment.

Submission should provide a GitHub source URL, a reachable demonstration URL, and the recorded video. No public URL has been created yet.
