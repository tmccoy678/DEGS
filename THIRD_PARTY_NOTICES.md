# Third-party source and acknowledgements

## Sashiko-derived files

Copyright 2026 The Sashiko Authors.

Source: [sashiko-dev/sashiko](https://github.com/sashiko-dev/sashiko), commit [39f6ce95c797bb40023247916a8b16d0f4aaf0da](https://github.com/sashiko-dev/sashiko/tree/39f6ce95c797bb40023247916a8b16d0f4aaf0da), `src/worker/kernel_workflow.rs`.

The Python operations in `sashiko_derived/__init__.py` are translated selections. Changes are the Python syntax and ownership representation, a decoded-object adapter, owned-subtree cloning, an alias guard, and extraction of the six relevant state fields. The two prompt text files retain their selected upstream contents verbatim. The Rust reference file assembles upstream excerpts with an original test harness. Exact ranges and hashes are in `provenance/sashiko-source.json`.

These portions are licensed under the [Apache License, Version 2.0](LICENSES/Apache-2.0.txt). Original notices are retained and modified files identify their changes. No root upstream NOTICE file was present in the inspected snapshot; this acknowledgement is additional provenance, not a substitute for the license. No ownership transfer or upstream endorsement is implied.

**Muchun Song** introduced the [dismissed-concern mechanism](https://github.com/sashiko-dev/sashiko/commit/39ff1c4d4a9e6fef466dfade79d34617c28f6cda) and the [conflict-resolution stage](https://github.com/sashiko-dev/sashiko/commit/522c14b7ac7461eecb2655c3d358afab4e5996b2). **Roman Gushchin** contributed the [declarative workflow implementation](https://github.com/sashiko-dev/sashiko/commit/87636aa3d648d272616154cfd673cb20dd762801). **Fuad Tabba** restored [review guidance](https://github.com/sashiko-dev/sashiko/commit/d9434ac3ca3abe47d308cfe7cb146a3f7dabf21b), and **Anders Heimer** contributed [location preservation](https://github.com/sashiko-dev/sashiko/commit/dc400a510f84d73062bc750490acb288e2281aaa). Credit also belongs to the wider Sashiko contributors; this is not an exhaustive authorship list.

## Chris Mason's review-prompts

Sashiko builds on [Chris Mason's review-prompts](https://github.com/masoncl/review-prompts), a separate project licensed under MIT with Copyright (c) 2025 Chris Mason. We acknowledge that foundation without attributing the selected Rust mechanisms solely to him. This draft does not vendor that separate prompt corpus. If it is later copied, its exact selected MIT copyright and permission notice must accompany the material. [Inspected license](https://github.com/masoncl/review-prompts/blob/032284304f3bbad50e092fa870c5d810de324d9f/LICENSE).

## Original DEGS and test tooling

The existing DEGS source and original draft integration/test code remain covered by the root MIT license, except for the explicitly identified Apache-derived portions above. The baseline manifest identifies the originally copied DEGS source. The optional Rust test harness uses pinned serde/serde_json dependencies recorded in its Cargo files; dependency sources and binaries are not bundled in this repository. Their own licenses continue to apply when building or redistributing them.

Kernel patches displayed by Sashiko and Sashiko's Linux submodule were not imported. The service's Apache license is not a license for every patch it displays.

## Benchmark corpus

The files in `benchmarks/data/` come from [json-schema-org/JSON-Schema-Test-Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/f6fd52a0a95472e079cbfc6ef7f089702b80e045), commit `f6fd52a0a95472e079cbfc6ef7f089702b80e045`. Copyright (c) 2012 Julian Berman. Distributed under MIT. The complete original [license](benchmarks/data/LICENSE) is included. Our runners, selection, and results are separate from the upstream test data. This notice does not change any existing project, source-port, or asset licensing.
