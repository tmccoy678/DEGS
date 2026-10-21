# Dobeworks Engineering Governance System — Engineering Charter

| Field | Value |
|---|---|
| Policy ID | `dobeworks-egs` |
| Version | `1.1.0` |
| Status | **ACTIVE** |
| Owner | Dobeworks |
| Steward | Taylor |

> **The Dobeworks Engineering Governance System is a tailored local engineering-governance framework informed by selected authoritative standards, handbooks, primary literature and public industry practices. It does not by itself constitute certification, accreditation, formal regulatory compliance, equivalence to private internal procedures, or endorsement by MIT, NASA, NIST, INCOSE, ISO, OWASP, CISA, Lockheed Martin, NVIDIA, Apple, Microsoft, IBM, the U.S. Department of Defense, or any other referenced organization.**

## Purpose and interpretation

This charter is the normative human-readable policy for Dobeworks EGS. A statement is normative only when it carries a stable `DEGS-*` identifier. Supporting documents elaborate these rules without creating a second source of truth. Controls are tailored proportionally to risk, but tailoring cannot erase a safety, authority, recovery, or approval boundary.

DEGS 1.1.0 is ACTIVE because the complete automated test suite passed, the independent governance audit remained `PASS_WITH_WARNINGS` with only O1/O4 explicitly accepted as non-critical historical limitations, and Taylor separately approved activation for the exact verified pre-activation artifact.

## Mission and requirements

- **DEGS-MISSION-001 — Mission and stakeholder intent.** Record the objective, stakeholder intent, and intended outcome before implementation.
- **DEGS-REQ-001 — Scope and non-goals.** State a bounded scope and explicit non-goals before work begins.
- **DEGS-REQ-002 — Measurable requirements.** Define measurable requirements and explicit acceptance criteria proportional to the task.
- **DEGS-REQ-003 — Assumptions.** Record material assumptions and test or resolve them when they can change the result.
- **DEGS-REQ-004 — Uncertainty.** State unknowns and uncertainty; never replace missing evidence with an unsupported value.
- **DEGS-ARCH-001 — Alternatives and trade-offs.** Consider credible alternatives and record consequential trade-offs before selecting a design.

## Architecture and configuration

- **DEGS-ARCH-002 — Smallest reversible design.** Prefer the smallest change that satisfies the requirement while preserving a credible rollback or recovery path.
- **DEGS-ARCH-003 — Operational elegance.** Apply clarity, cohesion, information hiding, simple interfaces, low unnecessary coupling, end-to-end correctness, reproducibility, observability, consistent naming, and removal of accidental complexity as derived design principles.
- **DEGS-ARCH-004 — Safety precedence.** Elegance never overrides safety, correctness, recoverability, or actual user needs.
- **DEGS-CFG-001 — Read-only baseline.** Capture the smallest sufficient read-only baseline before changing state.
- **DEGS-CFG-002 — Canonical source.** Maintain one identified canonical source of truth for controlled state; replicas and telemetry must name or derive from it.
- **DEGS-CFG-003 — One active writer.** Permit only one active writer in a configuration area at a time.
- **DEGS-CFG-004 — Backup and rollback.** Tier 2 and Tier 3 work requires a verified pre-change backup and an explicit rollback or recovery procedure.
- **DEGS-CFG-005 — Identifiable configuration.** Identify controlled configuration state by version and canonical path. For Tier 2 and Tier 3, bind reviewed, tested, execution, and handoff artifacts by a proportionate immutable identity such as SHA-256, signature, release digest, commit, or equivalent; record provenance and evidence freshness, and fail closed on unexplained identity mismatch.
- **DEGS-CFG-006 — Controlled change record.** Record each controlled change's version, timestamp, owner or agent, reason, risk tier, authority lane, affected files, backup, evidence, rollback, review, and final status. Maintain bidirectional requirement-to-artifact-to-test-to-evidence links and fail validation on unexplained orphan rules, artifacts, tests, or evidence.

## Risk and authority

- **DEGS-RISK-001 — Risk classification.** Classify the risk tier before any mutation using consequence, reversibility, data sensitivity, operational reach, physical effects, affected-party impact, and applicable AI or socio-technical risk. Unknown or unsupported risk fails closed.
- **DEGS-RISK-002 — Tier 2 and Tier 3 backup.** Verify a pre-change backup before Tier 2 or Tier 3 mutation.
- **DEGS-RISK-003 — Destructive approval.** Tier 3 or destructive work requires explicit, recorded Taylor approval before execution. A Tier 3 approval record must have `status=APPROVED`, `approver=Taylor`, `approver_role=HUMAN`, `approval_mode=OUT_OF_BAND`, and a non-empty evidence path. The gate validates this record structure but cannot independently prove human identity; a separate interactive human confirmation outside the evaluating agent remains required before execution.
- **DEGS-RISK-004 — Tier 3 containment.** Tier 3 work requires exact target identity, bounded blast radius, stop conditions, post-action validation, and no unresolved critical warning.
- **DEGS-RISK-005 — Verified recovery.** Verify recovery independently before deleting or consolidating backups, wiping a machine, or performing an irreversible operation.
- **DEGS-RISK-006 — Hazard elimination and residual-risk acceptance.** For safety-critical, physical, destructive, or irreversible work, identify credible hazards across the relevant lifecycle; eliminate them where practicable; mitigate and test what remains; check that a mitigation does not create an equal or greater hazard elsewhere; and record residual risk. Only Taylor acting as the separate human authority may accept residual risk through out-of-band evidence. An agent or evaluating model may analyze or recommend treatment but may not accept residual risk.
- **DEGS-AI-001 — Authority lane.** Select and record the correct authority lane before execution.
- **DEGS-AI-002 — Independent model fidelity.** Never silently substitute a provider, model, or role used for independent review or audit.
- **DEGS-AI-003 — No self-escalation.** An agent may not increase its own authority or reinterpret inconvenience as permission.
- **DEGS-AI-004 — AgentOps boundary.** AgentOps remains a deliberately delegated, non-administrator identity unless a separately approved and independently audited redesign changes that boundary.
- **DEGS-AI-005 — Taylor-reserved decisions.** Credentials, authentication, destructive approval, physical actions, value judgments, governance activation, and governance exceptions remain Taylor's decisions.
- **DEGS-AI-006 — AI lifecycle impact and assurance.** Before consequential AI-enabled work, record intended and unsupported uses, affected stakeholders, material data/model/tool provenance, foreseeable misuse, operating bounds, measurable quality, safety, security, and fairness criteria, Taylor's human decision role, override/stop/fallback/rollback paths, monitoring and reassessment triggers, limitations, and retirement or discontinuation criteria. Validate both components and the complete human-agent-tool system in representative and adversarial conditions proportional to risk. A gate result verifies recorded evidence only; it cannot authenticate Taylor, approve, execute, or activate work.

## Verification and validation

- **DEGS-VV-001 — Separation of V&V.** Distinguish verification of specified requirements from validation of the actual stakeholder and user need. Tier 2 and Tier 3 require separate passing verification and validation records with nonblank evidence paths.
- **DEGS-VV-002 — Positive tests.** Run positive tests appropriate to the change.
- **DEGS-VV-003 — Negative tests.** Run negative tests appropriate to the change, including denied access, malformed or out-of-distribution inputs, and foreseeable misuse when relevant.
- **DEGS-SEC-001 — Security tests.** Run security tests appropriate to the threat and risk tier. For agentic or AI-mediated work, cover applicable instruction injection, unauthorized tool use, dependency and egress boundaries, data poisoning or extraction, and control-bypass attempts.
- **DEGS-VV-004 — Failure paths.** Exercise failure paths, safe degradation, stop behavior, model/tool failure, emergent behavior, and human handoff appropriate to the change.
- **DEGS-VV-005 — Integration tests.** Run integration tests when the change crosses a real interface or subsystem boundary.
- **DEGS-VV-006 — Actual user path.** Validate the actual end-to-end user path, including the integrated human-agent-tool-data-permission boundary when applicable; a helper or unit test cannot substitute for that path.
- **DEGS-VV-007 — Independent review.** Consequential work requires review by a role or model independent of the task author, with reviewer identity, role, evidence, artifact identity, threat model, open-issue disposition, and remediation retest recorded where applicable. Metadata does not by itself prove cognitive independence.
- **DEGS-VV-008 — Tier 3 audit.** Tier 3 work requires an independent audit by a separate role or model and a dry run where possible.

## Security and data

- **DEGS-SEC-002 — Secret exclusion.** Exclude keys, passwords, tokens, authentication material, recovery material, and other secret values from prompts, reports, logs, fixtures, telemetry, and governance artifacts.
- **DEGS-SEC-003 — PRIVATE VAULT isolation.** PRIVATE VAULT remains outside all agent authority and may not be mounted or inspected by an agent.
- **DEGS-SEC-004 — Security-control preservation.** Do not weaken FileVault, SIP, Gatekeeper, encryption, recovery settings, credential permissions, or comparable controls merely to complete work.
- **DEGS-SEC-005 — Least authority.** Use the smallest permissions and authority necessary for the approved operation; arbitrary passwordless root is prohibited.
- **DEGS-SEC-006 — Enforcement outside the model control plane.** For AI-agent or model-mediated workflows, filesystem writes, command execution, network egress, dependency sources, secret access, and approval boundaries must be enforced by deterministic controls outside the evaluated model. Prompts, policy text, model self-reports, and model-based review may supplement but never replace those controls. Unknown or prompt-only enforcement fails closed; denial-path and post-change verification evidence are required.
- **DEGS-DATA-001 — Recovery before destructive data action.** No backup deletion, consolidation, disk erase, repartition, or computer wipe may proceed without independently verified recovery and explicit approval.
- **DEGS-DATA-002 — Physical evidence for storage decisions.** Never authorize a destructive storage decision using only apparent or logical size; verify the exact target and relevant physical allocation evidence.
- **DEGS-DATA-003 — Purpose limitation and data minimization.** Collect, expose, use, retain, and transfer only the minimum data necessary for an explicit authorized purpose. Record material provenance, rights or authority, retention, deletion or archival conditions, and access boundaries. Repurposing requires a newly recorded purpose and authority; unknown data authority fails closed. Prove that unnecessary data and secrets do not enter prompts, logs, fixtures, telemetry, or reports.

## Operations, completion, and context

- **DEGS-OPS-001 — Truthful completion.** Never claim completion merely because a command returned; report unmet criteria, warnings, and unknowns accurately. At every risk tier, derive the unresolved count from actual warning and unresolved-item records. Any nonzero count is critical, unresolved, and blocks readiness. A closed warning requires consistent `NONE` severity, `RESOLVED` status, `resolved: true`, and recorded nonblank closure evidence; malformed or contradictory states are invalid input.
- **DEGS-OPS-002 — Observability.** Provide proportionate post-deployment telemetry or status evidence without exposing secrets. Where monitoring applies, record its owner, expected operating range, alert and stop thresholds, reassessment triggers, and safe degradation or disengagement path.
- **DEGS-OPS-003 — Lessons become controls.** Convert a demonstrated exploit, failure, escaped defect, or other lesson into a regression test, checklist item, or policy rule when doing so materially reduces recurrence.
- **DEGS-OPS-004 — Proportional tailoring.** Apply enough governance to control the actual risk and avoid ceremony that cannot change a decision. Prototypes, canaries, rings, and staged rollout may reduce risk but never bypass applicable authority, backup, rollback, review, or evidence gates.
- **DEGS-OPS-005 — Source refresh.** Verify normative-source status at least every 90 days, before a major Tier 3 operation, and when a source announces a revision; never silently adopt a draft as normative. Pin living repositories to a commit and record retrieval identity for mutable pages used in a versioned baseline.
- **DEGS-OPS-006 — No false compliance claim.** Describe DEGS as informed by, mapped to, derived from, or consistent with selected public principles; do not claim certification, accreditation, compliance, approval, endorsement, equivalence, or access to private internal procedures without a qualified formal assessment.
- **DEGS-OPS-007 — Activation gate.** Activation requires the full automated suite, a passing independent governance audit or explicitly accepted non-critical warnings, and Taylor's explicit approval. Build success alone cannot change DRAFT to ACTIVE.
- **DEGS-OPS-008 — Definition of Done.** A task closes only after every applicable item in `DEFINITION_OF_DONE.md` has evidence or a permissible, documented waiver.
- **DEGS-CONTEXT-001 — Phase handoff.** Update canonical documentation and create a durable handoff before closing a phase.
- **DEGS-CONTEXT-002 — Trashpickup governance context.** At a phase boundary, `trashpickup` must record the current applicable DEGS version and status, applicable security invariants, relevant risk tier, authority lane, and unresolved governance warnings without implying activation.
- **DEGS-CONTEXT-003 — Treasurepickup governance continuity.** At fresh-context opening, `treasurepickup` must verify policy existence, version and status continuity, security-invariant continuity, and the next phase's authority lane before reporting readiness.

## Mentorship

- **DEGS-MENTOR-001 — Independent ownership.** Engineering guidance must increase Taylor's understanding and independent ownership rather than create avoidable dependence.
- **DEGS-MENTOR-002 — Guidance structure.** Consequential guidance must communicate objective, significance, evidence, assumptions, uncertainty, system model, risks, authority lane, approach, expected result, verification, lesson, and canonical next phase.
- **DEGS-MENTOR-003 — Action-feedback-reflection.** Use clear goals, constructive feedback, action-feedback-reflection cycles, and a concise teach-back or understanding check for important concepts.
- **DEGS-MENTOR-004 — Epistemic clarity.** Distinguish evidence, inference, and opinion; never manufacture certainty or use organizational prestige as a substitute for reasoning.
- **DEGS-MENTOR-005 — Human control.** Minimize unnecessary manual work while preserving Taylor's control over credentials, destructive approval, physical actions, and value judgments.

## Change and activation status

This is version `1.1.0`, status **ACTIVE**, with activation **AUTHORIZED** through `DEGS-DEC-007` and controlled change `DEGS-T3-ACTIVATION-20260901-011851`. The authoritative F1/F2 remediation re-audit remains **PASS_WITH_WARNINGS**; F1/F2 are resolved, R1/U1/U2 are closed by supervising verification, and R2 is resolved by the paired refresh. Taylor's warning acceptance remains limited to O1/O4. O2/O3 and F3/F6 remain resolved through `DEGS-DEC-006`. Policy activation does not authorize a governed task, exception, credential action, destructive action, physical action, or residual-risk acceptance. Changes follow `CHANGE_CONTROL.md`; superseded source records remain available for historical traceability.
