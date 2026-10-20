# DEGS — v2.1 

![DobeWorks command center running the current DobeWorks and DEGS cores](docs/figures/dobeworks-degs-command-center.png)

I built DobeWorks and DEGS for myself after I became obsessed with AI hallucination capture and immutable context transfer between windows. I believe that the resulting DobeWorks and DEGS that I was using on my MacPro are rigorous and true reflections of the diligence in the references of the work that they were built from.

DobeWorks and DEGS are my private personal engineering system and identity for methodological systems, software, research infrastructure, and special projects. It is not currently a public company identity, service, or commercial offering.

If you would like to discuss DobeWorks or DEGS privately, please email me at: tmccoy678@gmail.com.

Thank you,

Taylor

## Figures and references

[Read the illustrated system guide](docs/figures/README.md) for the relevant PDF figures and reflowable HTML equivalents. The [44-work APA reference edition](references/engineering-foundations-references.pdf) includes a [source-verification audit](references/verification.md).

## Public-data benchmark

**241 of 241 cases matched after the recursive equality correction. All 14 former false acceptances now reject correctly; the first run is preserved.** See [benchmark results and reproduction](benchmarks/benchmark.md).

DEGS evaluates engineering task records and explains whether their recorded evidence satisfies its rules. Missing recovery evidence or an agent's claimed human approval can block a task. A passing result does not prove the evidence true, approve the work, or execute it.

**Private development draft. No versioned public release.** This copy applies a bounded recursive JSON-equality correction to the standalone gate and adds a small, Sashiko-derived Python review-data component. It does not activate governance on your computer.

## Try the gate

Use an Apple-silicon Mac with Python 3.9 or later. Python 3.9.6 on macOS 26.6.2 was tested. No pip packages are needed for the gate or Python tests. Private repository access is currently required; run these commands from this checkout's root.

```sh
python3 -B bin/engineering-gate.py evaluate fixtures/tier2-complete-pass.json --json
python3 -B bin/engineering-gate.py evaluate fixtures/tier2-missing-rollback-blocked.json --json
python3 -B bin/engineering-gate.py evaluate fixtures/tier3-agent-self-approval-blocked.json --json
```

The examples are synthetic records. Their approval and evidence fields are examples, not authorization for real work.

| Example | Expected and observed | What it demonstrates |
| --- | --- | --- |
| Complete Tier 2 record | `PASS`, exit 0 | The supplied record meets the evaluated requirements. |
| Missing rollback evidence | `BLOCKED`, exit 2; `DEGS-CFG-004` | Recovery evidence is required for this task. |
| Agent self-approval | `BLOCKED`, exit 2; `DEGS-RISK-003` | An agent's claim does not satisfy the human-approval requirement. |

Each result lists the unmet fields and rule IDs. A blocked example is a successful demonstration when blocking is the expected result. Invalid JSON is a separate input failure (`FAIL`, exit 4), covered by the test suite.

## Try the Sashiko-derived component

```sh
python3 -B -m sashiko_derived.demo
```

This demonstration preserves a supplied concern and a supplied dismissed concern in separate collections, with the producing stage attached. It performs no LLM investigation and makes no decision about which claim is true. The later collections remain empty because deduplication, conflict resolution, and verification have not run.

The Python port retains Sashiko's selected state names, independent list defaults, deep-copy behavior, and stage stamping. Its object adapter distinguishes omitted arrays from explicit null. The original deduplication and conflict-resolution prompts are included as **unmodified reference text**, not an operating review service. See [source provenance](provenance/sashiko-source.json), [port boundaries](docs/port-boundaries.md), and [credits](THIRD_PARTY_NOTICES.md).

## Understand the tests

```sh
python3 -B -m unittest discover -s tests -v
```

The earlier run passed **64 tests**: 58 existing gate tests and 6 port tests. The current run passes **74 tests**, including three regression methods for recursive equality and seven for duplicate keys, invalid UTF-8, nonfinite JSON, excessive nesting, and malformed control values; five benchmark tests also pass. The tests exercise ordinary command input, valid and invalid records, required evidence, approval boundaries, and Python value semantics. A separate comparison passed **331 cases** against an executable harness containing the selected upstream Rust source. Instructions, raw outputs, source hashes, and exact environment are in [the test report](docs/test-report.md).

These results concern the recorded scenarios. They do not establish defect freedom, semantic truth, AI review accuracy, security certification, full-system integration, or support for other platforms. The copied core is identified in [the baseline manifest](provenance/degs-baseline.json). Local activation history, private audits, context-skill integration, and the Workbench adapter are excluded, along with tests requiring those dependencies. The policy rules remain unchanged. The comparator now distinguishes nested booleans from numbers; all 14 fixture CLI outputs remain identical. See the [correction record](docs/benchmark-correction.md) and [source identity](provenance/recursive-equality-correction.json).

An independent source-code review by [Nova (Muse Spark, Meta), 2026-10-05](docs/reviews/2026-10-05-nova.md) re-ran the suite under pytest (Python 3.12): **72 passed, 264 subtests passed, 0 failed**. No code was changed; no defects found. One documentation note: the `PASS_WITH_WARNINGS` → exit 1 convention could be stated once in the module docstring.

## Purpose, credit, and help

The goal is rigorous, understandable evidence with a clear explanation when something needs attention. Taylor welcomes questions, corrections, and suggestions and will respond as quickly as possible; no response-time guarantee is promised. Use this private repository's issues for non-sensitive questions. Follow [SECURITY.md](SECURITY.md) for vulnerability reports.

Muchun Song introduced Sashiko's dismissed-concern collection and concern/dismissed-concern conflict resolution. The implementation also credits the Sashiko contributors and Chris Mason's separate review-prompts foundation. [Exact contributions and licensing](THIRD_PARTY_NOTICES.md) distinguish those roles. [Citations](CITATIONS.md) explain the source and software-engineering literature behind the reporting format.

Existing DEGS material retains [MIT](LICENSE). Sashiko-derived files and reference prompts retain [Apache-2.0](LICENSES/Apache-2.0.txt), with notices and modifications identified separately. This is not a claim that every file has become Apache-2.0. Public v2.1 licensing, packaging, installation, and release acceptance remain unfinished.
