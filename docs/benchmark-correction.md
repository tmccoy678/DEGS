# Benchmark correction and validation scope

The first benchmark observation remains unchanged in [apple-silicon.json](../benchmarks/results/apple-silicon.json). The corrected observation is [apple-silicon-v3.json](../benchmarks/results/apple-silicon-v3.json); [comparison](../benchmarks/results/measurement-comparison-v3.json) records both run hashes and every changed case. Corpus pins, input bytes, labels, and denominators are unchanged. [Current test output](../benchmarks/results/validation-v3.json) retains commands, timestamps, exits, and diagnostics.

Both harnesses now preserve partial timeout diagnostics and actual script invocation arguments. The Observer stale control requires literal STALE freshness. Negative tests inject a real delayed process, contradictory freshness, broken candidates, and changed corpus/selection bytes. They failed for the intended reasons before the fixes and pass afterward. Python 3.9 cannot report original interpreter argv; the report records that limitation, the executable, effective interpreter flags, working directory, and exact script arguments.

## Core correction

A bounded change to the existing comparison helper compares nested JSON arrays and objects using an explicit worklist. Booleans differ from numbers at every nesting level; 1 equals 1.0; object key order is irrelevant; array order and length remain significant. Each queued pair visits a corresponding subtree, so total visits and maximum queued pairs are bounded by the finite input trees. An explicit worklist avoids consuming a Python call frame per nested level. Arbitrary Python objects, cycles, parser precision, nonfinite numbers, and expanded depth support are outside this correction. Existing parser/runtime limits are unchanged.

The first run matched 227/241 cases. The corrected run matches 241/241, including rejection of all 14 formerly accepted invalid examples. Review caught a depth regression in the first correction; 600-level array/object tests now cover numerical equality and boolean rejection through both schema keywords. Three added regression methods exercise both const and enum, mixed deeper nesting, scalar types, ordering, lengths, and every public failure. All 74 current core/port tests and five benchmark tests pass. Fourteen validate/evaluate fixture commands preserve byte-identical stdout/stderr and identical exit codes. The current schema uses scalar const/enum operands; no canonical task authority bypass was demonstrated.

The [original baseline manifest](../provenance/degs-baseline.json) remains unchanged. A [separate correction identity](../provenance/recursive-equality-correction.json) describes the new source. No third-party implementation was copied for this fix; existing MIT licensing remains. The previously tested Sashiko-derived component and its Apache notices remain unchanged.

## Remaining work

The user approved correction of staged system v1 and v2. The verified working pair is draftdobeworks/draftdegs, labeled v2.1 development drafts. A separate pre-Generation-2 staged v1 pair has not been identified. A component directory named v1 does not establish that system version. Apply the same behavioral regression and a minimal backport after its exact repository or commit is identified.

For the complete release, include the original integrated Trash Pickup, Treasure Pickup, and FigureMe. Preserve FigureMe's core behavior and visual essence while removing personal identifiers from release copies. The standalone Draft2Staged Pickup pair remains available independently. Packaging, accessible figure finalization, rights review, Apple-silicon fresh-user installation, and public publication are separate unfinished work. Nothing here changes repository visibility or qualifies a public release.

## Review correction history

The intermediate v2 observation is retained at [apple-silicon-v2.json](../benchmarks/results/apple-silicon-v2.json), with its [test output](../benchmarks/results/validation-v2.json). It passed the public subset but contained a newly discovered deep-container RecursionError. The v3 source uses an explicit worklist; new depth regressions failed on v2 before passing on the correction. The small public corpus alone did not reveal this regression. Current claims refer to v3.
