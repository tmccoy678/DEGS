# Tier 2 Required-Approval Correction

Date: 2026-10-22

## Observed defect

At commit `29632112ea809e7a589bf04031ecb433ec169888`, a schema-valid Tier 2 record could set:

```json
"human_approval": {
  "required": true,
  "status": "REJECTED"
}
```

and still receive `PASS` with exit status `0`. The schema accepted the record, but `tier2_controls` did not evaluate it.

## Historical context

Taylor's account is that DobeWorks and DEGS once governed every message entering the regular Codex terminal. As the system became increasingly exacting, ordinary work accumulated disproportionate gate preparation. The fail-open Tier 2 behavior functioned as an escape from that condition, and a separate external clean Workbench lane later made the need for balance unmistakable.

That history explains the behavior but does not make the verdict truthful. Proportional governance belongs in risk classification and control selection. Once a task record says human approval is required and records `REJECTED`, the gate must block.

The DobeWorks repository preserves [two screenshots and their provenance](https://github.com/tmccoy678/DobeWorks/blob/main/docs/history/clean-path-balance.md): a contemporaneous September 8 discussion of the governance burden and an October 22 documentation capture of the installed external Workbench menu showing the resulting Clean Path option. The latter was opened solely for the visual record and does not indicate use on that date.

## Correction

`tier2_controls` now applies `DEGS-RISK-003` when `human_approval.required` is `true`. Only exact `status=APPROVED` satisfies that Tier 2 requirement. The existing stronger Tier 3 checks for Taylor, human role, out-of-band mode, and evidence remain unchanged.

Regression tests cover both sides of the boundary:

- required plus `REJECTED` returns `BLOCKED`, exit `2`;
- required plus `APPROVED` retains `PASS`, exit `0` when every other Tier 2 control passes.

The design lesson remains `DEGS-OPS-004`: apply enough governance to control the actual risk and avoid ceremony that cannot change a decision. A gate can stay quiet during ordinary work while remaining exact when it emits a verdict.
