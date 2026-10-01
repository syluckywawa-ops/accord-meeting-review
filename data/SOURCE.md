# Data provenance

## Source

- Dataset: AMI Meeting Corpus, manual annotations v1.6.2
- Official corpus page: <https://groups.inf.ed.ac.uk/ami/corpus/>
- Official download page: <https://groups.inf.ed.ac.uk/ami/download/>
- Official scenario partition: <https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml>
- Official annotation-presence table: <https://groups.inf.ed.ac.uk/ami/corpus/annotationpresent.shtml>
- Download URL: <https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip>
- Downloaded archive size: 22,887,865 bytes
- SHA-256: `b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d`
- Licence: CC BY 4.0 for the relevant publicly released transcription and annotations; attribution must remain in the final repository and report.

## Scope used by ActionAI

Only manual word transcripts, segment links, participant/meeting metadata, and abstractive action summaries are required. Audio and video are out of scope and are not downloaded.

`data/exploratory_v11/` contains one additional derived transcript and turn-metadata file, ES2002a, for a 2 October 2026 product-only manual workflow check. It is outside the locked 23-meeting experiment manifest and does not alter that dataset or its scores. The same AMI source archive, checksum, and CC BY 4.0 attribution apply.

The repository does not commit the 22 MB source archive or its extracted copy. A reproducible preparation script will verify the SHA-256 value and generate the derived transcript files and manifest statistics.

## Important interpretation

The AMI annotation category named “individual actions” concerns physical movements and gestures. It is not the follow-up-work target in this project. ActionAI uses manually identified future commitments, with the abstractive `<actions>` section consulted only after initial labels are locked as an independent audit reference.
