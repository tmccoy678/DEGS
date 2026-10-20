# Dobeworks EGS Engineering Gate

The gate at `bin/engineering-gate.py` evaluates readiness and completion evidence. It uses Python 3's standard library only and never executes the described task.

## Inputs

A JSON task record conforming to `gate.schema.json`. Relative evidence paths are reported as recorded; version 1.1.0 does not authenticate their contents. Reviewers must examine consequential evidence independently.

Commands:

```bash
python3 bin/engineering-gate.py validate <task.json>
python3 bin/engineering-gate.py evaluate <task.json>
python3 bin/engineering-gate.py explain <task.json>
```

Add `--json` anywhere after the script name for machine-readable output.

## Private companion Workbench assurance selector

The private `TAYLOR_AI_WORKBENCH` integration's bounded DEAS adapter
(`bin/deas-gate.py`) is excluded from this public snapshot. Its `adoption`
and `work-unit` commands are therefore unavailable in this checkout.

The adapter returns `ADOPTION` source/configuration identity or
`WORK_UNIT_SELECTION` profile/overlay selection. Exit `0` is PASS, `2` is
BLOCKED, and `3` is malformed-input or validator ERROR. It is read-only and
does not inspect DEGS task evidence. Its PASS is not DEGS readiness, overall
DEAS conformance, evidence validation, task authority, acceptance,
qualification, integration, promotion, merge, release, or deployment.

## Outputs

Every result includes:

- decision;
- unmet requirements;
- sanitized warnings;
- applicable DEGS rule IDs;
- risk tier;
- authority lane; and
- recorded evidence paths.

`explain` also maps each applicable rule ID to a concise explanation.

## Decisions and exit codes

| Decision | Exit | Meaning |
|---|---:|---|
| `PASS` | 0 | Applicable recorded controls are present with no unresolved warning. |
| `PASS_WITH_WARNINGS` | 1 | Controls pass and at least one non-critical warning remains. |
| `BLOCKED` | 2 | A required readiness or completion control is absent or an unresolved critical warning exists. |
| `FAIL` | 3 | The risk tier is unknown/unsupported or evaluation otherwise fails closed. |
| invalid input/schema | 4 | Input is unreadable, malformed, unsupported, or contains prohibited secret-like telemetry/state fields. The JSON decision remains `FAIL`. |

## Risk-specific enforcement

- **Tier 0:** objective, explicit read-only scope, Command Center lane, and controlled secret exposure.
- **Tier 1:** bounded scope, requirements, acceptance criteria, baseline, static and positive tests, rollback or a reason it is trivial, and handoff.
- **Tier 2:** Tier 1 controls plus backup, explicit rollback, an evidenced `risk_analysis` covering consequence, reversibility, data sensitivity, operational reach, physical effects, affected-party impact, and AI/socio-technical risk; `deterministic_controls`; exact `artifact_identity` across reviewed/tested/execution/handoff artifacts with configuration version, canonical path, provenance, and current evidence; complete `change_traceability`; `data_governance`; a current `threat_model`; consequential `ai_assurance` with measurable quality/safety/security/fairness criteria; operational `monitoring`; separate `verification` and `validation` records with `PASS` or `VERIFIED` status and a nonblank `evidence_path`; negative/security/failure-path/end-to-end tests whose passing records each include a nonblank `evidence_path`; independent review; canonical documentation; and sanitized telemetry.
- **Tier 3:** Tier 2 controls plus the Taylor lane; a complete `hazard_analysis` with tested elimination or mitigation, a passing cross-domain check, and human-only evidenced residual-risk acceptance; an approval record with `status=APPROVED`, `approver=Taylor`, `approver_role=HUMAN`, `approval_mode=OUT_OF_BAND`, and a non-empty evidence path; independently verified recovery; independent audit; exact target; bounded blast radius; stop conditions; post-action validation; dry run where possible; and no unresolved critical warning.

`data_governance`, `threat_model`, `ai_assurance`, and `monitoring` allow reasoned non-applicability: `applicable=false`, `status=NOT_APPLICABLE`, and a non-empty reason. Omission, unknown authority, prompt-only controls, stale identity evidence, or an unsupported assertion of non-applicability fails closed. `deterministic_controls`, `artifact_identity`, and `change_traceability` remain mandatory for Tier 2 and Tier 3.

`validate` applies the complete canonical JSON schema with a dependency-free validator. `evaluate` and `explain` preserve rule-specific BLOCKED diagnostics for intentionally incomplete negative records, but a record that would otherwise pass is rejected as invalid unless it also conforms to the schema. The planned JSON template is schema-valid; its `PENDING` controls are not readiness evidence and will not pass evaluation.

Required readiness text must contain a non-whitespace character. Scope descriptions, requirements, acceptance criteria, target and blast-radius descriptions, stop conditions, rollback procedures, recovery references, approval references, and dry-run evidence or non-applicability reasons are checked for their required types and nonblank content. A list containing only blank strings does not satisfy a control. The data-authority sentinel `UNKNOWN` is rejected after trimming whitespace and ignoring case, including for repurposing authority. These checks validate the submitted record; they do not authenticate the referenced evidence or approval.

A declared top-level task status of `FAILED` or `BLOCKED` is an authoritative stop signal under `DEGS-OPS-001`: an otherwise passing evaluation returns `BLOCKED` with exit code 2. `PLANNED`, `READY_FOR_EXECUTION`, `IN_PROGRESS`, and `COMPLETE` remain evidence-driven; a declaration never converts unmet evidence into a pass.

An independent review record for Tier 2 and Tier 3 identifies `task_author` and a different reviewer, the reviewer role, evidence, open-issue disposition, and a passing retest. Submitted metadata cannot by itself prove cognitive independence.

Unknown risk fails closed. A Tier 3 fixture PASS means readiness evaluation only; the fixture cannot authorize or execute destructive work.

The engineering gate's lane map has task-record evaluation scope and accepts direct human `TAYLOR` records at Tier 1 and Tier 2. The context helper has a distinct, stricter phase-boundary context-routing scope: Tier 1 and Tier 2 route through Workbench or deliberately delegated AgentOps, while Taylor is reserved for Tier 3 human decisions. See `AUTHORITY_LANES.md`; the distinction grants no new permission.

## Examples

```bash
python3 bin/engineering-gate.py evaluate fixtures/tier0-readonly-pass.json --json
python3 bin/engineering-gate.py evaluate fixtures/tier2-missing-rollback-blocked.json --json
python3 bin/engineering-gate.py explain fixtures/tier3-complete-dry-run-pass.json
```

## Interpretation limitations

The gate provides evidence-based governance assistance but does not replace professional judgment. It checks the shape and recorded status of evidence, not the truth, sufficiency, independence, or technical quality of every referenced artifact. The Tier 3 approval check validates record structure only; it cannot cryptographically authenticate Taylor or independently prove human identity. Tier 3 execution still requires a separate interactive human confirmation outside the evaluating agent. The gate never executes a task and does not establish certification, compliance, safety-critical suitability, approval, or execution authority.
