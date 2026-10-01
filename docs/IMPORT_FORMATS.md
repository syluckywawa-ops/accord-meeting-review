# Document import and transcription status

TXT, text-based PDF and DOCX are parsed on the local server. File size is limited to 8 MB; extracted text to 150,000 characters; PDF to 100 pages. Uploading a document only prepares an editable preview. The reviewer must inspect the text and explicitly start action extraction.

PDF extraction is not OCR. Scanned pages are reported, not silently assumed to be processed. Password-protected PDFs are rejected. DOCX main-body paragraphs and table cells are extracted in XML order. Headers, footers, comments and tracked changes are not a reliable source for this prototype. Legacy DOC is not supported. Complex layouts can lose speaker relationships; reviewers should repair the preview.

Audio is not currently implemented. A transcription provider or local model must be selected and installed before the interface may claim audio support. Speaker diarization is a separate capability: ordinary transcription must not invent participant names. Real transcription should preserve uncertain owners and provide timestamps; transcript quotes are not proof of the original audio without listening checks.

New document imports are product trials, not additions to the frozen AMI test evaluation. Private uploads and review sessions are excluded from Git via `.gitignore`.

Public deployment is pending. The current Python local server cannot be directly published to the Sites Workers runtime without porting the backend or selecting a Python hosting service. Public deployment also needs authentication, upload limits, rate limits, storage isolation and a budget gate for live extraction; do not expose an unrestricted paid API key. GitHub publication needs a verified destination/account and a source/data/license/secret audit first.
