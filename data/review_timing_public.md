# Five-meeting review timing observations

**Reviewer: Lin Siyuan.** These are meeting-level observations from the review timing workbook. The reviewer confirmed on 1 October 2026 that all five sessions were on **29 September 2026**, after the frozen few-shot outputs were generated. The workbook had mistakenly recorded 27 September; its session dates and start/finish date portions were corrected in a preserved new copy. Clock times, pauses, formulas, counts, and net minutes were not changed. Exact start/finish clock times are omitted from this repository summary; the corrected workbook's SHA-256 is recorded in `outputs/final-analysis/final_comparison.json`.

| Meeting | Words | Few-shot status | Predictions | Gross min | Pause min | Net min | Final actions | Added | Removed | Modified | Evidence corrections | Difficulty |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES2004d | 7,337 | Invalid | 0 | 66 | 0 | 66 | 1 | 1 | 0 | 0 | 0 | Hard |
| ES2014a | 2,522 | Valid | 1 | 26 | 0 | 26 | 4 | 3 | 0 | 1 | 0 | Medium |
| IS1009b | 6,831 | Invalid | 0 | 47 | 0 | 47 | 0 | 0 | 0 | 0 | 0 | Hard |
| TS3003c | 5,245 | Valid | 3 | 83 | 15 | 68 | 3 | 1 | 1 | 2 | 0 | Medium |
| TS3007d | 9,713 | Valid | 2 | 96 | 0 | 96 | 2 | 1 | 1 | 1 | 1 | Hard |
| **Total** | **31,648** |  | **6** | **318** | **15** | **303** | **10** | **6** | **2** | **4** | **1** |  |

The procedure was to inspect each frozen candidate against its cited transcript evidence, scan the complete meeting for missed work, correct the approved list, and stop the timer after finishing. An invalid output required manual reconstruction or confirmation of no action. This is a descriptive single-reviewer workload observation, **not** a controlled comparison with manual-only note taking and not evidence of time saved by AI. See `docs/EVALS_EXPLAINER.md` for how it relates to the formal extraction scores.
