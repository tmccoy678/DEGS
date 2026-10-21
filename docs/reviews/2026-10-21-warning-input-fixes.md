# Warning and input corrections — October 21, 2026 (UTC)

This change implements findings 1–4 of the preserved [DEGS core review](agentverify-2027-degs-core/README.md) at base commit `30c93fa6bb05bad56504d8b666ea407491be7720`. It strengthens warning readiness at every tier, preserves accepted numbers exactly, rejects unsupported number representations and unpaired Unicode surrogates, and makes human output readable. Finding 5 remains outside this correction.

## Corrected behavior

| Finding | Current behavior | Regression seam |
| --- | --- | --- |
| 1 — contradictory resolution | Closure requires exact `NONE`, `RESOLVED`, `true`, and a nonblank evidence reference. Missing, contradictory, padded, or unknown warning states produce input `FAIL`, exit `4`, even when another control already blocks. | Actual CLI across all tiers and commands |
| 2 — unresolved-item bypass | The gate derives the count from every active warning and unresolved-item entry. A positive count is aggregate `CRITICAL`, `UNRESOLVED`, and `false`; every tier blocks. Output entries are numbered and retain source indexes. | Actual CLI: strings, structured records, mixed history, caller-supplied zero, malformed severity, and existing unmet controls |
| 3 — numeric information loss | Integer and finite decimal input is parsed without a binary-float intermediate. Tokens exceeding 4,300 digits or an absolute explicit exponent of 10,000 reject before numeric construction. Tighter interpreter integer limits remain active. | Loader and actual CLI: precision, underflow, bounds, equivalent constants, nonfinite tokens, and Boolean distinction |
| 4 — Unicode/output failure | Every decoded key and string value rejects unpaired surrogates. Valid Unicode and paired escapes remain supported. Machine JSON stays sorted and ASCII-safe; human warnings and state use labeled lines, with escapes when the terminal cannot encode a character. | Actual CLI: all commands, both formats, nested keys/values, valid Unicode, and ASCII-only output |

`unresolved_items` remains a list of actual records, not a caller-supplied number. The output's `warning_state.unresolved_count` is the derived number. Closed records belong in `warnings` history. A zero count removes only the warning block. `validate` remains structural; a valid active record can pass validation while readiness evaluation blocks. The historical `PASS_WITH_WARNINGS` exit-code mapping remains reserved, but active warnings no longer produce that decision.

See the [gate contract](../../ENGINEERING_GATE.md#warning-and-unresolved-item-policy) and [numeric input policy](../numeric-input-policy.md). Closure evidence references are checked for presence and shape; their truth is not authenticated.

## Verification

Host: macOS 27.0.1, arm64. The source remained unchanged through the recorded tests. Python's standard library supplied the implementation and tests; no dependencies were installed.

| Check | Result |
| --- | --- |
| Full gate, equality, and Sashiko-derived suite — Python 3.14.7 | 102 passed |
| Same suite — Python 3.9.6 | 101 passed, 1 skipped |
| Benchmark harness — Python 3.14.7 | 5 passed |
| Fresh v5 schema-helper benchmark | 241/241 matched; controls passed; zero failures |

Python 3.9 lacks the configurable integer-conversion-limit API, so its corresponding test skips; that test passes on Python 3.14. The benchmark retains its frozen selection and 273 excluded cases. It measures the schema helper, while the separate CLI regressions exercise the corrected task-input behavior. No Rust comparison was rerun.

A separate Codex agent reviewed the implementation and policy documents and found no blocking defect. Its independent mixed-history probes returned `BLOCKED`, count `2`, and correctly numbered source indexes at all four tiers. This is an agent source review, not a human audit.

The companion [DobeWorks integration record](https://github.com/tmccoy678/DobeWorks-v3.0/blob/main/docs/reviews/2026-10-21-warning-input-integration.md) records 10 passing frontend tests against these gate bytes. The default sibling checkout is now `DEGS-v3.0`; an explicit checkout override retains that selected gate's behavior.

## Evidence record

- **Evidence ID:** DEGS-WARNING-INPUT-FIXES-20261021
- **Requirement/fault IDs:** Core review findings 1–4; `DEGS-OPS-001`; exact bounded numeric input and Unicode scalar-value input contracts.
- **Claim under test:** The reproduced warning, numerical-loss, and Unicode failure paths reject or block as specified; valid recorded closure, supported numbers, and valid Unicode retain their intended outcomes.
- **Acceptance method:** Failing regressions before implementation; final public-CLI and loader tests; existing suites; pinned benchmark; source review and artifact identity checks.
- **Exact source/configuration/role/device-safe identity/environment/target:** Base commit above; before/after source maps and interpreter identities in the raw record; macOS arm64 local synthetic task evaluation. Core SHA-256 `ed5e485b1e2e50e5d3ff5eb8b49b5cab10e442928425666ca850266d41771ce0`.
- **Procedure or command identity:** Exact argument arrays in the raw record: unittest discovery under `tests` on both interpreters; discovery under `benchmarks` and `benchmarks/run_benchmark.py --output benchmarks/results/apple-silicon-v5.json` on Python 3.14.7.
- **Start time:** 2026-10-21T03:09:35.608651+00:00
- **End time:** 2026-10-21T03:10:18.753751+00:00
- **Clock-quality basis:** Host UTC wall clock; independent synchronization not measured.
- **Expected result:** All supported checks pass; malformed representations fail closed; source hashes remain unchanged.
- **Actual result:** All final commands exited `0`; test and benchmark outcomes are in the table above. Unittest's normal progress and success report appears on stderr and is retained verbatim. Benchmark stderr was empty.
- **Status:** PASS for the stated checks; delivery identities are established separately through Git and the pull request.
- **Discrepancy references:** Findings 1–4 corrected within this scope; finding 5 remains open.
- **Artifact paths:** [Raw verification](2026-10-21-warning-input-fixes-evidence.json), [sorted correction manifest](2026-10-21-warning-input-fixes-sha256.txt), [v5 benchmark](../../benchmarks/results/apple-silicon-v5.json), and the tests named in the raw source map.
- **Cryptographic identities:** Raw verification SHA-256 `2d71af0f0fc2697b1cb575f818ba5c5a8fa16a54a3d6501c43923093884aee25`; v5 report SHA-256 `a197dc3785a7b9d013a174427befbca5f26d962e2e118653f2c1b429f28580ff`; changed-artifact identities in the sorted manifest.
- **Evidence owner:** Taylor; prepared by Codex and its scoped review/verification agents.
- **Human/physical action owner:** Not applicable to local synthetic tests.
- **Confidentiality classification:** Public source, synthetic records, benchmark data, and local test execution metadata.
- **Recoverability classification:** Reversible source changes; baseline bytes retained in Git. Revert the correction to restore its predecessor.
- **Limitations:** One host; two tested Python versions; benchmark subset; an evidence reference does not authenticate closure; broader approval and tier-classification changes are not implemented here.
- **Unsupported inferences:** These checks do not establish evidence truth, authenticated human identity, task execution authority, certification, or production qualification.
- **Current freshness:** Fixed observation for the recorded source bytes; later relevant changes require renewed verification.
- **Supersession:** This record supplies current-source claims. The original review, earlier verification records, historical activation metadata, and v1–v4 benchmark artifacts remain unchanged.

The raw record preserves available original warning red-phase output. Numeric and Unicode red-phase observations are explicitly labeled summaries because their original raw logs were not retained.
