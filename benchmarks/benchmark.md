# DEGS schema-helper benchmark

**The current v4 run matched 241 of 241 cases. Zero false acceptances, false rejections, exceptions, or timeouts. Controls passed.**

This measures the existing schema helper against independently labeled JSON Schema examples. It does not measure the full DEGS gate, authority decisions, security effectiveness, or full draft2020-12 compliance.

The original run exposed one recursive JSON-equality defect across 14 cases: Python container equality accepted nested booleans as numbers. The historical v3 correction rejected all 14 examples while preserving numerical equivalence such as 1 and 1.0, object member ordering independence, and array ordering. The original 227/241 result and the v3 correction evidence remain unchanged. At that correction, all 14 fixture CLI invocations retained identical exits and diagnostics; that historical comparator benchmark demonstrated no canonical task authority bypass. The current v4 observation measures the gate after the October task-input boundary fixes and retains the same 241/241 corpus result.

Selection was frozen before execution: 69 groups across 15 complete upstream files, comprising 107 valid and 134 invalid cases. Results: 107/107 valid cases correctly accepted; 134/134 invalid cases correctly rejected. Another 273 cases in those files were excluded for unsupported schema syntax. Other files and optional directories were outside scope; their inventory is recorded in the raw report. An omitted case is not a pass. See the [selection rationale](selection.md) for exact group indices and limitations.

## Reproduce on Apple silicon

From this repository root, with Python 3:

```bash
python3 -B benchmarks/run_benchmark.py --output benchmarks/results/rerun.json
python3 -B -m unittest discover -s benchmarks -p 'test_*.py' -v
```

Exit 0 is expected for the corrected candidate when all selected cases and controls pass. The original candidate exited 1 for fourteen failures and wrote a complete report. Harness exit 1 indicates measured mismatches or failed controls; exit 2 indicates input/configuration error. A failed control invalidates interpretation of the corpus score. Each candidate process has a five-second timeout. There are no automatic retries. Corpus and selection integrity must pass before scoring. The fixed selection manifest is hashed in the harness; changing it creates a new benchmark version and must be disclosed.

Current v4 host: macOS 27.0.1, arm64, Python 3.14.7. The run started 2026-10-20T21:02:03.658248+00:00 and ended 2026-10-20T21:02:11.633984+00:00. Its recorded candidate SHA-256 matches the current gate. Current verification also passes 79 core/port tests and five benchmark tests, with test coverage under Python 3.14.7 and Python 3.9.6; see the [October boundary-fix record](../docs/reviews/2026-10-20-boundary-fixes.md).

Historical v3 host: macOS 26.6.2, arm64, Python 3.9.6. That run started 2026-09-11T20:10:59.022826+00:00 and ended 2026-09-11T20:11:06.193573+00:00. Each observation concerns its recorded source and environment. Other platforms remain unverified; these results are not a performance leaderboard or certification.

## Inspect the evidence

- [Current v4 machine-readable run](results/apple-silicon-v4.json): all case outcomes, stdout/stderr, exits, controls, identities, and environment.
- [Historical v3 comparator run](results/apple-silicon-v3.json): preserved evidence for the recursive-equality correction.
- [Original observation, preserved unchanged](results/apple-silicon.json). Its command field was a hard-coded recipe; later runs record actual script arguments and interpreter state.
- [Historical before/after comparison](results/measurement-comparison-v3.json): exact changed outcomes and run hashes for the comparator correction.
- [Current source and test verification](../docs/reviews/2026-10-20-boundary-fixes.md).
- [Historical correction scope and limitations](../docs/benchmark-correction.md).
- [Pinned input manifest](manifest.json): upstream commit and exact input SHA-256 hashes.
- [Selection and research](selection.md): source fit, exclusions, and license inspection.
- [Full upstream MIT notice](data/LICENSE): retained unchanged with the copied data.
- [Original APA reference collection](../references/dobeworks-apa-references.pdf): unchanged; benchmark sources supplement it.

Source: [json-schema-org/JSON-Schema-Test-Suite at the pinned commit](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/f6fd52a0a95472e079cbfc6ef7f089702b80e045). Credit Julian Berman and JSON Schema Test Suite contributors. No endorsement is implied. Only selected data files and the license were copied; the report distinguishes local controls from public inputs. DobeWorks-v2.1 and DEGS-v2.1 are public development snapshots without a versioned release.

## Originally failed cases, now corrected

| Case ID (file:group:test) | Upstream expectation | Original result | Corrected result |
| --- | --- | --- | --- |
| `enum.json:6:1` | Invalid | Accepted | Rejected |
| `enum.json:6:2` | Invalid | Accepted | Rejected |
| `enum.json:8:1` | Invalid | Accepted | Rejected |
| `enum.json:8:2` | Invalid | Accepted | Rejected |
| `enum.json:10:0` | Invalid | Accepted | Rejected |
| `enum.json:12:0` | Invalid | Accepted | Rejected |
| `const.json:6:1` | Invalid | Accepted | Rejected |
| `const.json:6:2` | Invalid | Accepted | Rejected |
| `const.json:7:1` | Invalid | Accepted | Rejected |
| `const.json:7:2` | Invalid | Accepted | Rejected |
| `const.json:8:1` | Invalid | Accepted | Rejected |
| `const.json:8:2` | Invalid | Accepted | Rejected |
| `const.json:9:1` | Invalid | Accepted | Rejected |
| `const.json:9:2` | Invalid | Accepted | Rejected |

[Evidence contract and change controls](evidence.md).

Timeouts retain partial stdout and stderr. Invocation provenance records executable, script arguments, working directory, and effective interpreter flags; original interpreter arguments are unavailable on Python 3.9. Corpus inputs and denominators are unchanged.

During the historical comparator correction, independent review found that the intermediate recursive implementation could raise RecursionError on deeply nested but previously supported JSON. The current comparator retains the explicit worklist; its 600-level array and object regressions pass valid numeric comparisons and reject nested booleans. [The intermediate observation](results/apple-silicon-v2.json) is preserved but does not describe the current source.
