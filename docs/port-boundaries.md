# Scope of the faithful Python port

The source is Sashiko commit `39f6ce95c797bb40023247916a8b16d0f4aaf0da`. Exact file and excerpt hashes are recorded in the source manifest.

- `append_stage_dismissed_concerns` preserves every JSON value, deep-clones nested values, stamps objects with the producing stage, overwrites an existing stage, and preserves order. Scalars remain scalars.
- `append_stage_items` additionally supplies the default type when the original type is absent, non-string, or empty. A whitespace-only string is preserved, matching Rust. The unused `_key` parameter remains recognizable.
- The three output types preserve field names and independent empty list defaults. `from_mapping` is explicitly limited to decoded JSON objects: omitted fields default empty, null or non-array known fields fail, unknown fields are ignored, and array items remain untyped JSON values.
- This object adapter is not a translation of the complete upstream model-response extraction or JSON text deserializer. It does not reproduce Markdown-fence extraction, duplicate JSON-key parsing, arbitrary top-level serialized sequences, or every numeric-parser limit. Direct dataclass construction, like direct Rust struct construction, is not that adapter.
- Inputs to value operations must be finite, acyclic, JSON-compatible values representable by `serde_json::Value`; strings passed as stage/default type have the corresponding Rust string role. Arbitrary Python objects are outside this interface. No evidence schema or semantic verification is added by these helpers.
- JSON cloning creates independent owned subtrees even when a Python caller supplies repeated references to the same mutable container. The port uses recursive JSON-value copying because memoized `deepcopy` would preserve aliases that Rust `Value` does not have. Cyclic data and arbitrary Python objects remain outside the declared interface.
- Python rejects identical source and destination lists before appending. Rust's borrowing rules prohibit that simultaneous mutable/immutable alias; the guard prevents a Python-only unbounded loop. This is a disclosed language adaptation.
- `ReviewState` contains only the six selected collections. It is not the full `KernelReviewState`, and it does not implement persistence or an immutable audit ledger.
- Deduplication and conflict-resolution prompt text is copied verbatim. No prompt execution, automatic authority, final severity filter, or early-exit orchestration was imported. The prompt words are not deterministic validation.

The original source verifier for stage concerns returns success without checking the item contents. The selected port does not disguise that limitation by calling its output proven or accepted. A future semantic-review integration must preserve all existing DEGS requirements and document its separate verification evidence.

The differential harness compares selected operations on decoded JSON values and objects, including null, booleans, scalars, nested arrays/objects, Unicode, and signed/unsigned integer limits. It is bounded evidence, not a proof over every input or an end-to-end Sashiko port.

## Review-state command boundary

`bin/review-state.py` is an original DEGS command adapter around the selected
Sashiko-derived value operations. It accepts one closed
`degs.sashiko-review-request/v1` object, limits the request to 32 stage outputs
and one MiB, rejects duplicate keys or stage names, bounds JSON depth, node
count, and number representation, rejects non-finite numbers, validates stage
names, and returns one `degs.sashiko-review-state/v1` object.

The result records `report_basis: AGENT_SUPPLIED_REVIEW_VALUES` and one of two
states:

- `UNRESOLVED_REPORTED`: at least one supplied concern remains in
  `all_concerns`.
- `NONE_REPORTED`: no unresolved concern was supplied.

`NONE_REPORTED` does not mean clean, verified, accepted, or complete. The
command cannot detect an omitted concern or decide whether a dismissal is
sound. Its deduplication, conflict-resolution, and findings collections remain
empty because the corresponding semantic stages are not executed. Callers
must retain the distinction between this aggregation result, DEGS preflight
readiness, candidate state, and human acceptance.
