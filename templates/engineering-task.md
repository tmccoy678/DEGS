# DEGS Engineering Task

## Identity

- Task ID:
- Task author:
- Title:
- Schema version: 1
- Status: PLANNED

## Objective

## Stakeholders

## Scope

## Non-goals

## Authority lane

## Risk tier

## Requirements

## Acceptance criteria

## Assumptions and uncertainty

## Security invariants

## Read-only baseline

## Alternatives and trade-offs

## Selected design

## Affected files

## Pre-change backup

## Rollback or recovery

## Risk analysis

For Tier 2 and Tier 3, record status, summary, evidence path, and explicit assessments of consequence, reversibility, data sensitivity, operational reach, physical effects, affected-party impact, and AI or socio-technical risk.

## Deterministic control boundaries

For Tier 2 and Tier 3, record externally enforced filesystem-write, command-execution, network-egress, dependency-source, secret-access, and approval boundaries, denial tests, and post-change verification. Unknown or prompt-only state blocks.

## Exact artifact identity

Record the configuration version, canonical path, identity method, reviewed identifier, tested identifier, execution identifier, handoff identifier, common-match result, provenance, evidence-freshness status/basis/time, and evidence path.

## Change traceability

Link each requirement to the changed artifact, tests, and evidence. Record the orphan count; Tier 2 and Tier 3 require zero.

## Data governance

Record applicability, purpose, owner, classes, minimum-necessary fields, provenance, authority, retention, deletion or archival conditions, access boundary, and any separately authorized repurposing. If not applicable, record `NOT_APPLICABLE` and a reason.

## Current threat model

Record applicability, threats, mitigations, evidence, and confirmation that review occurred after the last material change. If not applicable, record `NOT_APPLICABLE` and a reason.

## Consequential AI assurance

Record applicability, intended and unsupported uses, affected stakeholders, provenance, foreseeable misuse, operating bounds, and measurable quality, safety, security, and fairness criteria. Each criterion records a measure, threshold, and evidence path. Also record Taylor's human decision paths, representative/adversarial/handoff tests, monitoring and reassessment, limitations, and retirement. If not applicable, record `NOT_APPLICABLE` and a reason.

## Monitoring and safe degradation

Record applicability, owner, expected operating range, alert thresholds, stop thresholds, reassessment triggers, safe degradation, and evidence. If not applicable, record `NOT_APPLICABLE` and a reason.

## Hazard analysis and residual risk

For Tier 3, list hazards, elimination or mitigation controls, passing test evidence, and a cross-domain check. Any accepted residual risk requires separate Taylor `HUMAN` and `OUT_OF_BAND` acceptance evidence.

## Tests

Every required passing test record must include `status: PASS` and a nonblank `evidence_path`.

### Static

### Positive

### Negative

### Security

### Failure path

### Integration

### Actual end-to-end user path

## Verification

- Verification status (`PASS` or `VERIFIED` for Tier 2 and Tier 3):
- Evidence path:

## Validation

- Validation status (`PASS` or `VERIFIED` for Tier 2 and Tier 3):
- Evidence path:

## Independent review or audit

- Task author:
- Reviewer:
- Reviewer role:
- Open-issues status:
- Retest status:
- Evidence path:

## Taylor approval

- Status:
- Approver:
- Approver role (`HUMAN` or `AGENT`):
- Approval mode (`OUT_OF_BAND` or `IN_BAND`):
- Evidence path:
- Separate interactive human confirmation outside the evaluating agent:

For Tier 3, the gate requires `APPROVED`, `Taylor`, `HUMAN`, `OUT_OF_BAND`, and a non-empty evidence path. This record does not cryptographically authenticate Taylor or independently prove human identity, and the gate never executes the task.

## Recovery validation

## Exact target identity

## Bounded blast radius

## Stop conditions

## Post-action validation

## Dry run

## Sanitized telemetry

## Canonical documentation

## Handoff

## Warnings

Each warning must record canonical `severity`, `status`, and `resolved` fields. Active warnings use `INFO`, `WARNING`, or `CRITICAL` with `UNRESOLVED` and `false`; all block readiness. Closed warning history requires `NONE`, `RESOLVED`, `true`, and a nonblank closure `evidence_path`.

## Unresolved items

List the actual unresolved records as nonblank text or active warning objects. The gate derives the count and numbers output items. Any nonzero count blocks readiness at every tier; move resolved records to warning history instead of leaving them here.

## Final status
