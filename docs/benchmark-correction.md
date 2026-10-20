# Benchmark correction and validation scope

The first benchmark observation remains unchanged in [apple-silicon.json](../benchmarks/results/apple-silicon.json). The historical recursive-equality correction is recorded in [apple-silicon-v3.json](../benchmarks/results/apple-silicon-v3.json); [comparison](../benchmarks/results/measurement-comparison-v3.json) records both run hashes and every changed case. Corpus pins, input bytes, labels, and denominators are unchanged. [Historical v3 test output](../benchmarks/results/validation-v3.json) retains commands, timestamps, exits, and diagnostics. These records identify the September comparator generation, not later task-input or readiness-control changes. The [October boundary-fix record](reviews/2026-10-20-boundary-fixes.md) identifies the newer source and verification scope.

Both harnesses now preserve partial timeout diagnostics and actual script invocation arguments. The Observer stale control requires literal STALE freshness. Negative tests inject a real delayed process, contradictory freshness, broken candidates, and changed corpus/selection bytes. They failed for the intended reasons before the fixes and pass afterward. Python 3.9 cannot report original interpreter argv; the report records that limitation, the executable, effective interpreter flags, working directory, and exact script arguments.

## Core correction

A bounded change to the existing comparison helper compares nested JSON arrays and objects using an explicit worklist. Booleans differ from numbers at every nesting level; 1 equals 1.0; object key order is irrelevant; array order and length remain significant. Each queued pair visits a corresponding subtree, so total visits and maximum queued pairs are bounded by the finite input trees. An explicit worklist avoids consuming a Python call frame per nested level. Arbitrary Python objects, cycles, parser precision, nonfinite numbers, and expanded depth support are outside this correction. Existing parser/runtime limits are unchanged.

The first run matched 227/241 cases. The historical corrected run matched 241/241, including rejection of all 14 formerly accepted invalid examples. Review caught a depth regression in the first correction; 600-level array/object tests cover numerical equality and boolean rejection through both schema keywords. Three added regression methods exercise both const and enum, mixed deeper nesting, scalar types, ordering, lengths, and every public failure. The v3 evidence records 67 core/port tests and five benchmark tests passing. At that correction, fourteen validate/evaluate fixture commands preserved byte-identical stdout/stderr and identical exit codes. The schema used scalar const/enum operands; no canonical task authority bypass was demonstrated by that comparator benchmark.

The [original baseline manifest](../provenance/degs-baseline.json) remains unchanged. A [separate correction identity](../provenance/recursive-equality-correction.json) describes the historical comparator source with SHA-256 `cdaf77937cbe54a7611825edddd9502a058245a933ef3fae683870d28de0bbde`. It is not the identity of subsequent gate revisions. No third-party implementation was copied for that fix; existing MIT licensing remains. The Sashiko-derived component and its Apache notices remain unchanged.

## Remaining work

The public working pair is DobeWorks-v2.1 and DEGS-v2.1, published as development snapshots. A separate pre-Generation-2 staged v1 pair has not been identified. A component directory named v1 does not establish that system version. A backport requires identification of that exact repository or commit.

The complete integrated product remains separate work, including Trash Pickup, Treasure Pickup, and FigureMe. The standalone Pickup pair remains independently available. Packaging, installation acceptance, and integrated release qualification remain outside these component corrections. Public source availability does not qualify an operational system.

## Review correction history

The intermediate v2 observation is retained at [apple-silicon-v2.json](../benchmarks/results/apple-silicon-v2.json), with its [test output](../benchmarks/results/validation-v2.json). It passed the public subset but contained a newly discovered deep-container RecursionError. The v3 source uses an explicit worklist; new depth regressions failed on v2 before passing on the correction. The small public corpus alone did not reveal this regression. Claims in this historical comparator section refer to v3; later source identities and results are recorded separately.
