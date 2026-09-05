# Synthetic issue ledger

Scope: one-page project-owned LaTeX baseline and revision. This ledger records
build and review evidence; it does not assess scientific correctness or journal
acceptance.

| ID | Area | Observation | Evidence | State |
| --- | --- | --- | --- | --- |
| SYN-001 | Source identity | The baseline and revision are distinct, frozen source files. | SHA-256 values in `evidence/build-manifest.json` | Verified |
| SYN-002 | Clean builds | Baseline and revision compile independently with the recorded TeX toolchain. | `pdf/baseline.pdf`, `pdf/revision.pdf`, final logs | Passed |
| SYN-003 | Redline | `latexdiff` 1.4.0 generates a third source that compiles independently. | `redline/redline.tex`, `pdf/redline.pdf`, final log | Passed |
| SYN-004 | References | The final logs contain no undefined-reference warning. | Three final logs and build manifest | Passed |
| SYN-005 | Visible layout | The final logs contain no overfull-box warning in this one-page example. | Three final logs | Passed |
| SYN-006 | Change review | The redline exposes changes to the abstract, method, equation, table, added verification section, and conclusion. | `pdf/redline.pdf` | Reviewable |
| SYN-007 | Content authority | The synthetic wording makes no scientific claim; content approval remains with the author in a real sprint. | Baseline, revision, and packet boundary | Not delegated |

Unresolved build blockers in this synthetic sample: **0**.
