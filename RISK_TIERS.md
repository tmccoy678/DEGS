# Dobeworks EGS Risk Tiers

`DEGS-RISK-001` requires classification before mutation and fails closed for unknown or unsupported tiers. Controls accumulate: each tier includes all applicable controls below it.

At every tier, any active warning or unresolved item blocks readiness under `DEGS-OPS-001`. The gate derives and numbers these items; a nonzero count is `CRITICAL`, `UNRESOLVED`, and `resolved: false`. Closure requires consistent `NONE` / `RESOLVED` / `true` fields and a nonblank evidence reference. See the [warning policy](ENGINEERING_GATE.md#warning-and-unresolved-item-policy).

## Tier 0 — Read-only / observation

Examples: inspect state, read logs, or create analysis inside an authorized report directory.

Required controls:

- objective;
- bounded scope;
- explicit read-only confirmation;
- controlled secret exposure; and
- documented findings and uncertainty.

Default lane: Command Center.

## Tier 1 — Reversible workspace change

Examples: source-code edits, new reports, test fixtures, or documentation.

Required controls:

- baseline;
- requirements and acceptance criteria;
- appropriate static and positive tests;
- Every required passing test record includes `status: PASS` and a nonblank `evidence_path`;
- rollback, or an explicit reason rollback is trivial; and
- handoff.

Default lane: Taylor AI Workbench; AgentOps only through deliberate delegation within existing authority.

## Tier 2 — Configuration / integration change

Examples: launchers, provider routing, agent definitions, permission policy, startup configuration, services, or deployment configuration.

Required controls:

- all applicable Tier 1 controls;
- verified pre-change backup;
- explicit rollback;
- risk analysis;
- deterministic filesystem, command, network-egress, dependency-source, secret-access, and approval boundaries enforced outside the model;
- exact reviewed-to-executed artifact identity and complete change traceability;
- purpose-limited, minimum-necessary data governance when applicable;
- a current post-change threat model when applicable;
- consequential-AI assurance when applicable;
- monitoring thresholds, reassessment triggers, and safe degradation when applicable;
- Separate passing verification and validation records with nonblank evidence paths;
- positive, negative, security, and failure-path tests;
- actual end-to-end user-path test;
- independent review;
- canonical documentation; and
- sanitized telemetry or status update.

Default lane: Taylor AI Workbench. AgentOps requires deliberate delegation and may not increase its authority.

## Tier 3 — Critical / destructive / irreversible

Examples: deleting or consolidating backups, erasing or repartitioning disks, wiping a computer, disabling security controls, changing encryption or recovery settings, destructive database migration, or broad privilege escalation.

Required controls:

- all applicable Tier 2 controls;
- complete hazard analysis with tested elimination or mitigation and a passing cross-domain check;
- any residual risk accepted only by Taylor as a HUMAN, out of band, with evidence;
- an explicit Taylor approval record with `status=APPROVED`, `approver=Taylor`, `approver_role=HUMAN`, `approval_mode=OUT_OF_BAND`, and a non-empty evidence path;
- independently verified recovery path;
- dry run where possible;
- independent audit by a separate role or model;
- exact target identity;
- bounded blast radius;
- stop conditions;
- post-action verification;
- no unresolved critical warning; and
- no unattended execution by default.

Authority lane: Taylor. The gate validates approval-record structure; it does not cryptographically authenticate Taylor or otherwise prove human identity. Tier 3 execution still requires a separate interactive human confirmation outside the evaluating agent. Gate PASS means readiness evidence is present; the gate never executes or authorizes the action by itself.
