# Boundary fixes and verification — October 20, 2026

This correction makes required readiness controls reject the reproduced blank and mistyped values, and restores unknown-authority rejection after whitespace padding. Its predecessor is commit `50289ead9c286a24175b6748921e3ae709d844d5`.

The changes were written manually after failing CLI regressions. [Raw evidence](2026-10-20-boundary-fixes-evidence.json) records exact commands, times, exits, stdout/stderr, and final source identities. The sorted [correction manifest](2026-10-20-boundary-fixes-sha256.txt) identifies changed artifacts. Git delivery identities remain separate from this immutable package.

## Repairs

| Review finding | Corrected behavior | Regression evidence |
| --- | --- | --- |
| G1 — malformed required controls passed | Required objectives, scope descriptions, requirement/criterion lists, rollback procedures, containment text, stop conditions, and evidence references require the appropriate nonblank types. Tier 3 post-action validation and successful rehearsal require evidence references. | Added CLI regression methods cover the repaired controls and planned-template behavior across `validate`, `evaluate`, and `explain`. |
| G2 — padded UNKNOWN authority passed | Primary and repurposing authority reject UNKNOWN after trimming whitespace and ignoring case. | Case and whitespace variants reject, retaining rule-specific data-governance diagnostics. |
| G3 — historical evidence described as current | Documentation identifies the older recursive-equality generation and directs current-source claims to this record and the fresh v4 benchmark. | Historical files are retained byte-for-byte; the fresh benchmark's gate digest matches the corrected executable. |

The schema keeps the PLANNED template structurally valid. Readiness evaluation still rejects unmet controls. This preserves the distinction between recording a plan and satisfying the evaluated requirements. Existing rule IDs and the non-executing gate interface remain intact.

## Recorded verification

Host: macOS 27.0.1, build 26A434, Apple silicon arm64. Python 3.14.7 ran in a temporary virtual environment without pip or system site packages; Python 3.9.6 used the system interpreter. Test processes used temporary HOME/TMPDIR and a restricted environment. No dependencies were installed.

| Suite | Python 3.14.7 | Python 3.9.6 |
| --- | ---: | ---: |
| Gate, recursive equality, and Sashiko-derived data operations | 79 passed | 79 passed |
| Benchmark harness tests | 5 passed | 5 passed |

All suites exited 0. The seven included fixture outcomes remain covered by the gate tests. The [fresh v4 benchmark](../../benchmarks/results/apple-silicon-v4.json) matched 241/241 selected cases with controls passing, exit 0, and empty stderr. Its gate SHA-256 is `8b687a92cb607be9e03223e1c17d7bbf419a60b0593446d2cd3fa2d6cbe4e0e0`.

The benchmark measures the schema helper's predeclared supported-keyword subset. Its 273 excluded cases remain excluded and are not counted as passes. Full-gate malformed-control behavior is exercised by the separate CLI regression tests.

Independent read-only source reviews found no remaining blocking findings in the corrected controls. Changed/extracted production functions satisfy the 60-line bound. Historical provenance, source-port files, corpus pins, licenses, and original benchmark observations are unchanged.

## Evidence and authority boundaries

The gate checks the shape and recorded status of submitted evidence. A nonblank evidence reference is not authentication of its contents, and the human-approval record check does not authenticate Taylor. The gate still does not approve or execute the described task.

DobeWorks's historical validators retain their older external gate pin. This source correction does not repin them or establish a tested current integration. The optional Rust comparison was not rerun because the toolchain was unavailable; the unchanged port's earlier 331-case result remains historical evidence.

## Evidence record

- **Evidence ID:** DEGS-BOUNDARY-FIXES-20261020
- **Requirement/fault IDs:** G1, G2, G3; DEGS-REQ-002, DEGS-RISK-004, DEGS-DATA-003
- **Claim under test:** Required malformed readiness records and padded unknown authority cannot receive a passing evaluation through the reproduced paths.
- **Acceptance method:** Regression-first CLI tests, existing unit suites, pinned schema-helper benchmark, source inspection, and independent review.
- **Exact source/configuration/role/device-safe identity/environment/target:** Base commit above; final source identities and environment in the raw evidence; changed-artifact identities in the correction manifest.
- **Procedure or command identity:** Exact command arrays in the raw evidence; documented unittest discovery and benchmark commands.
- **Start time:** 2026-10-20T20:58:52.005166+00:00
- **End time:** 2026-10-20T21:02:11.643892+00:00
- **Clock-quality basis:** Host wall-clock UTC timestamps; independent synchronization not verified.
- **Expected result:** Malformed required controls reject; reasoned PLANNED placeholders remain structurally valid but do not satisfy readiness; valid controls and benchmark cases pass.
- **Actual result:** 79 unit tests and 5 benchmark tests passed on each interpreter; 241/241 selected benchmark cases and controls passed.
- **Status:** PASS for the stated component checks.
- **Discrepancy references:** Reproduced G1, G2, and G3 corrected within this scope.
- **Artifact paths:** docs/reviews/2026-10-20-boundary-fixes-evidence.json; docs/reviews/2026-10-20-boundary-fixes-sha256.txt; benchmarks/results/apple-silicon-v4.json.
- **Cryptographic identities:** Sorted correction manifest and raw evidence source_sha256 map; historical identities remain unchanged.
- **Evidence owner:** Taylor; Codex prepared this correction and verification record.
- **Human/physical action owner:** Taylor; no physical or live-system action performed.
- **Confidentiality classification:** Public source, public benchmark corpus, and synthetic task records.
- **Recoverability classification:** Original Git history and exact baseline backup retained; revert the bounded correction to restore its predecessor.
- **Limitations:** Component checks on one host; supported-keyword benchmark subset; optional Rust comparison not rerun; no current DobeWorks integration test.
- **Unsupported inferences:** Evidence truth, authenticated human identity, task approval, execution authority, certification, or production readiness.
- **Current freshness:** Fixed observation for the identified source bytes; rerun affected checks after relevant source or configuration changes.
- **Supersession:** Current-source claims use this record; historical comparator observations and manifests remain unchanged.
