import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "bin" / "engineering-gate.py"
FIXTURES = ROOT / "fixtures"
SCHEMA = ROOT / "gate.schema.json"
TASK_TEMPLATE = ROOT / "templates" / "engineering-task.json"
CHARTER = ROOT / "ENGINEERING_CHARTER.md"


class EngineeringGateCliTests(unittest.TestCase):
    def run_gate(self, command, task_path):
        completed = subprocess.run(
            [sys.executable, str(GATE), command, str(task_path), "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertTrue(completed.stdout, completed.stderr)
        payload = json.loads(completed.stdout)
        return completed, payload

    def run_payload(self, command, payload=None, raw_text=None, raw_bytes=None):
        with tempfile.TemporaryDirectory() as directory:
            task_path = Path(directory) / "task.json"
            if raw_bytes is not None:
                task_path.write_bytes(raw_bytes)
            elif raw_text is not None:
                task_path.write_text(raw_text, encoding="utf-8")
            else:
                task_path.write_text(json.dumps(payload), encoding="utf-8")
            return self.run_gate(command, task_path)

    def fixture_payload(self, name):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def unmet_rule_for_field(self, payload, field):
        matching = [
            item["rule_id"]
            for item in payload["unmet_requirements"]
            if item["field"] == field
        ]
        self.assertEqual(len(matching), 1, payload["unmet_requirements"])
        return matching[0]

    def test_tier0_readonly_fixture_passes(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier0-readonly-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")
        self.assertEqual(payload["risk_tier"], "TIER_0")
        self.assertEqual(payload["authority_lane"], "COMMAND_CENTER")
        self.assertEqual(payload["unmet_requirements"], [])
        self.assertIn("DEGS-RISK-001", payload["applicable_rule_ids"])

    def test_tier1_reversible_fixture_passes(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier1-reversible-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")
        self.assertEqual(payload["risk_tier"], "TIER_1")
        self.assertIn("DEGS-VV-001", payload["applicable_rule_ids"])

    def assert_control_rejected(self, fixture, path, value):
        for command in ("validate", "evaluate", "explain"):
            with self.subTest(fixture=fixture, path=path, value=value, command=command):
                task = self.fixture_payload(fixture)
                parent = task
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                completed, payload = self.run_payload(command, payload=task)
                self.assertEqual(completed.stderr, "")
                self.assertEqual(completed.returncode, 4 if command == "validate" else 2)
                self.assertEqual(payload["decision"], "FAIL" if command == "validate" else "BLOCKED")
                self.assertTrue(any(
                    item["field"].split(".", 1)[0].split("[", 1)[0] == path[0]
                    for item in payload["unmet_requirements"]
                ), payload)

    def test_readiness_rejects_blank_or_mistyped_planning_controls(self):
        for fixture in (
            "tier0-readonly-pass.json", "tier1-reversible-pass.json",
            "tier2-complete-pass.json", "tier3-complete-dry-run-pass.json",
        ):
            for path, value in (
                (("objective",), " "), (("objective",), 0),
                (("scope",), {"description": " "}),
                (("scope",), {"description": 0}),
                (("scope",), {"read_only": True}),
            ):
                self.assert_control_rejected(fixture, path, value)
            if fixture != "tier0-readonly-pass.json":
                for field in ("requirements", "acceptance_criteria"):
                    for value in ([""], ["valid", " "], [0], []):
                        self.assert_control_rejected(fixture, (field,), value)

    def test_planned_placeholders_validate_but_cannot_pass_readiness(self):
        for path in (("objective",), ("scope", "description"), ("requirements",), ("acceptance_criteria",)):
            with self.subTest(path=path):
                task = self.fixture_payload("tier1-reversible-pass.json")
                task["status"] = "PLANNED"
                parent = task if len(path) == 1 else task[path[0]]
                parent[path[-1]] = [" "] if path[0] in {"requirements", "acceptance_criteria"} else " "
                completed, payload = self.run_payload("validate", payload=task)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(payload["decision"], "PASS")
                for command in ("evaluate", "explain"):
                    completed, payload = self.run_payload(command, payload=task)
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertEqual(payload["decision"], "BLOCKED")

    def test_readiness_rejects_malformed_recovery_and_rollback_controls(self):
        for fixture in ("tier1-reversible-pass.json", "tier2-complete-pass.json", "tier3-complete-dry-run-pass.json"):
            for value in (0, " "):
                self.assert_control_rejected(fixture, ("rollback",), {"status": "VERIFIED", "procedure": value})
                if fixture == "tier1-reversible-pass.json":
                    self.assert_control_rejected(fixture, ("rollback",), {"required": False, "reason": value})
                else:
                    self.assert_control_rejected(fixture, ("backup", "evidence_path"), value)

    def test_tier3_readiness_rejects_malformed_containment_and_evidence(self):
        fixture = "tier3-complete-dry-run-pass.json"
        for path in (
            ("target_identity", "identifier"), ("blast_radius", "description"),
            ("recovery_validation", "evidence_path"), ("human_approval", "evidence_path"),
            ("post_action_validation", "evidence_path"), ("dry_run", "evidence_path"),
        ):
            for value in (0, " "):
                self.assert_control_rejected(fixture, path, value)
        for value in ([""], ["valid", " "], [0], []):
            self.assert_control_rejected(fixture, ("stop_conditions",), value)
        for value in (0, " "):
            self.assert_control_rejected(fixture, ("dry_run",), {"applicable": False, "reason": value})
        for field, value in (
            ("post_action_validation", {"status": "PASS"}),
            ("dry_run", {"applicable": True, "performed": True, "status": "PASS"}),
        ):
            self.assert_control_rejected(fixture, (field,), value)

    def test_unknown_data_authority_cannot_be_hidden_by_case_or_whitespace(self):
        for field in ("authority", "repurposing"):
            for value in ("UNKNOWN", "unknown", " UNKNOWN ", "\tUnKnOwN\n"):
                if field == "repurposing":
                    value = {
                        "planned": True, "status": "AUTHORIZED", "purpose": "Synthetic reuse",
                        "authority": value, "evidence_path": "synthetic-reuse.json",
                    }
                self.assert_control_rejected(
                    "tier2-complete-pass.json", ("data_governance", field), value
                )

    def test_tier1_unmet_controls_report_governing_rule_ids(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task["requirements"] = []
        task["tests"]["positive"] = []
        task["rollback"] = {"required": True, "status": "MISSING"}
        task["handoff"] = {"status": "MISSING"}

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "requirements"), "DEGS-REQ-002"
        )
        self.assertEqual(
            self.unmet_rule_for_field(payload, "tests.positive"), "DEGS-VV-002"
        )
        self.assertEqual(
            self.unmet_rule_for_field(payload, "rollback"), "DEGS-ARCH-002"
        )
        self.assertEqual(
            self.unmet_rule_for_field(payload, "handoff"), "DEGS-CONTEXT-001"
        )

    def test_tier1_informational_rule_list_matches_applicable_controls(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier1-reversible-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("DEGS-RISK-002", payload["applicable_rule_ids"])
        self.assertIn("DEGS-ARCH-002", payload["applicable_rule_ids"])
        self.assertIn("DEGS-VV-002", payload["applicable_rule_ids"])
        self.assertIn("DEGS-CONTEXT-001", payload["applicable_rule_ids"])

    def test_tier2_missing_rollback_is_blocked(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier2-missing-rollback-blocked.json"
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertTrue(
            any(item["field"] == "rollback" for item in payload["unmet_requirements"])
        )
        self.assertEqual(
            self.unmet_rule_for_field(payload, "rollback"), "DEGS-CFG-004"
        )

    def test_tier2_risk_analysis_requires_all_classification_factors(self):
        valid = {
            "status": "PASS",
            "factors": {
                "consequence": "Configuration readiness only; no execution authority.",
                "reversibility": "Verified backup and explicit rollback are present.",
                "data_sensitivity": "Synthetic, non-sensitive fixture data only.",
                "operational_reach": "Bounded to the local synthetic fixture.",
                "physical_effects": "None; evaluator does not execute work.",
                "affected_party_impact": "Taylor receives readiness evidence only.",
                "ai_socio_technical_risk": "Human authority and misuse paths are recorded.",
            },
            "summary": "Synthetic Tier 2 evidence with bounded local consequence.",
            "evidence_path": "fixture",
        }
        for case in ("missing_factor", "blank_factor", "missing_evidence"):
            with self.subTest(case=case):
                task = self.fixture_payload("tier2-complete-pass.json")
                task["risk_analysis"] = json.loads(json.dumps(valid))
                if case == "missing_factor":
                    task["risk_analysis"]["factors"].pop("physical_effects")
                elif case == "blank_factor":
                    task["risk_analysis"]["factors"]["data_sensitivity"] = ""
                else:
                    task["risk_analysis"]["evidence_path"] = ""

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "risk_analysis"),
                    "DEGS-RISK-001",
                )

    def test_tier2_complete_fixture_passes(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier2-complete-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")

    def test_tier2_and_tier3_require_verification_evidence(self):
        for fixture_name in (
            "tier2-complete-pass.json",
            "tier3-complete-dry-run-pass.json",
        ):
            for case in (
                "missing",
                "blank_path",
                "non_passing",
                "lowercase_pass",
                "lowercase_verified",
            ):
                with self.subTest(fixture=fixture_name, case=case):
                    task = self.fixture_payload(fixture_name)
                    if case == "missing":
                        task.pop("verification")
                    elif case == "blank_path":
                        task["verification"]["evidence_path"] = "   "
                    elif case == "non_passing":
                        task["verification"]["status"] = "FAIL"
                    else:
                        task["verification"]["status"] = case.removeprefix(
                            "lowercase_"
                        )

                    completed, payload = self.run_payload("evaluate", payload=task)

                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertEqual(payload["decision"], "BLOCKED")
                    self.assertEqual(
                        self.unmet_rule_for_field(payload, "verification"),
                        "DEGS-VV-001",
                    )

    def test_tier2_and_tier3_require_validation_evidence(self):
        for fixture_name in (
            "tier2-complete-pass.json",
            "tier3-complete-dry-run-pass.json",
        ):
            for case in (
                "missing",
                "blank_path",
                "non_passing",
                "lowercase_pass",
                "lowercase_verified",
            ):
                with self.subTest(fixture=fixture_name, case=case):
                    task = self.fixture_payload(fixture_name)
                    if case == "missing":
                        task.pop("validation")
                    elif case == "blank_path":
                        task["validation"]["evidence_path"] = "   "
                    elif case == "non_passing":
                        task["validation"]["status"] = "FAIL"
                    else:
                        task["validation"]["status"] = case.removeprefix(
                            "lowercase_"
                        )

                    completed, payload = self.run_payload("evaluate", payload=task)

                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertEqual(payload["decision"], "BLOCKED")
                    self.assertEqual(
                        self.unmet_rule_for_field(payload, "validation"),
                        "DEGS-VV-001",
                    )

    def test_tier2_and_tier3_accept_verified_vv_evidence(self):
        for fixture_name in (
            "tier2-complete-pass.json",
            "tier3-complete-dry-run-pass.json",
        ):
            for field in ("verification", "validation"):
                with self.subTest(fixture=fixture_name, field=field):
                    task = self.fixture_payload(fixture_name)
                    task[field]["status"] = "VERIFIED"

                    completed, payload = self.run_payload("evaluate", payload=task)

                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(payload["decision"], "PASS")
                    self.assertEqual(payload["unmet_requirements"], [])

    def test_tier2_deterministic_boundaries_fail_closed(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        cases = {
            "missing": None,
            "prompt_only": {
                "status": "VERIFIED",
                "enforced_outside_model": False,
                "boundaries": {
                    name: {"status": "PROMPT_ONLY", "mechanism": "Model instruction"}
                    for name in (
                        "filesystem_write",
                        "command_execution",
                        "network_egress",
                        "dependency_sources",
                        "secret_access",
                        "approval",
                    )
                },
                "denial_test": {"status": "PASS", "evidence_path": "fixture"},
                "post_change_verification": {
                    "status": "PASS",
                    "evidence_path": "fixture",
                },
                "evidence_path": "fixture",
            },
            "unknown": {
                "status": "VERIFIED",
                "enforced_outside_model": True,
                "boundaries": {
                    name: {
                        "status": "UNKNOWN" if name == "network_egress" else "ENFORCED",
                        "mechanism": "Synthetic external control",
                    }
                    for name in (
                        "filesystem_write",
                        "command_execution",
                        "network_egress",
                        "dependency_sources",
                        "secret_access",
                        "approval",
                    )
                },
                "denial_test": {"status": "PASS", "evidence_path": "fixture"},
                "post_change_verification": {
                    "status": "PASS",
                    "evidence_path": "fixture",
                },
                "evidence_path": "fixture",
            },
        }
        for case, control in cases.items():
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                if control is None:
                    task.pop("deterministic_controls", None)
                else:
                    task["deterministic_controls"] = control

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "deterministic_controls"),
                    "DEGS-SEC-006",
                )

    def test_tier2_artifact_identity_and_change_traceability_fail_closed(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        valid_identity = {
            "status": "VERIFIED",
            "method": "SHA256",
            "configuration_version": "synthetic-v1",
            "canonical_path": "synthetic://controlled-config",
            "reviewed_identifier": "sha256:fixture",
            "tested_identifier": "sha256:fixture",
            "execution_identifier": "sha256:fixture",
            "handoff_identifier": "sha256:fixture",
            "match": True,
            "provenance": "Locally authored synthetic fixture.",
            "evidence_freshness": {
                "status": "CURRENT",
                "verified_at": "2026-08-31T19:00:00-05:00",
                "basis": "Identity checked in this test run.",
            },
            "evidence_path": "fixture",
        }
        valid_traceability = {
            "status": "VERIFIED",
            "orphan_count": 0,
            "links": [
                {
                    "requirement": "Synthetic requirement",
                    "artifact": "synthetic-config.json",
                    "tests": ["synthetic gate test"],
                    "evidence_path": "fixture",
                }
            ],
            "evidence_path": "fixture",
        }
        cases = {
            "identity_mismatch": ("artifact_identity", "DEGS-CFG-005"),
            "missing_tested_identity": ("artifact_identity", "DEGS-CFG-005"),
            "missing_handoff_identity": ("artifact_identity", "DEGS-CFG-005"),
            "missing_provenance": ("artifact_identity", "DEGS-CFG-005"),
            "stale_identity_evidence": ("artifact_identity", "DEGS-CFG-005"),
            "orphaned_traceability": ("change_traceability", "DEGS-CFG-006"),
        }
        for case, (field, rule_id) in cases.items():
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["artifact_identity"] = json.loads(json.dumps(valid_identity))
                task["change_traceability"] = json.loads(
                    json.dumps(valid_traceability)
                )
                if case == "identity_mismatch":
                    task["artifact_identity"]["execution_identifier"] = (
                        "sha256:different"
                    )
                    task["artifact_identity"]["match"] = False
                elif case == "missing_tested_identity":
                    task["artifact_identity"].pop("tested_identifier")
                elif case == "missing_handoff_identity":
                    task["artifact_identity"].pop("handoff_identifier")
                elif case == "missing_provenance":
                    task["artifact_identity"]["provenance"] = ""
                elif case == "stale_identity_evidence":
                    task["artifact_identity"]["evidence_freshness"]["status"] = (
                        "STALE"
                    )
                else:
                    task["change_traceability"]["orphan_count"] = 1

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(self.unmet_rule_for_field(payload, field), rule_id)

    def test_tier2_data_purpose_authority_and_repurposing_fail_closed(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        valid = {
            "applicable": True,
            "status": "VERIFIED",
            "purpose": "Exercise the gate with synthetic fixture metadata.",
            "owner": "Taylor",
            "data_classes": ["Synthetic governance metadata"],
            "necessary_fields": ["Control status and evidence paths"],
            "minimum_necessary": True,
            "provenance": "Locally authored synthetic fixture.",
            "authority": "Taylor",
            "retention": "Retain with the versioned test suite.",
            "deletion_or_archival_conditions": "Archive with a superseded policy.",
            "access_boundary": "Canonical governance fixture directory.",
            "repurposing": {"planned": False},
            "evidence_path": "fixture",
        }
        cases = ("unknown_authority", "unauthorized_repurposing", "not_minimized")
        for case in cases:
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["data_governance"] = json.loads(json.dumps(valid))
                if case == "unknown_authority":
                    task["data_governance"]["authority"] = "UNKNOWN"
                elif case == "unauthorized_repurposing":
                    task["data_governance"]["repurposing"] = {
                        "planned": True,
                        "status": "PENDING",
                        "purpose": "A new purpose",
                        "authority": "Taylor",
                        "evidence_path": "fixture",
                    }
                else:
                    task["data_governance"]["minimum_necessary"] = False

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "data_governance"),
                    "DEGS-DATA-003",
                )

    def test_tier2_stale_or_incomplete_threat_model_is_blocked(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        valid = {
            "applicable": True,
            "status": "CURRENT",
            "reviewed_after_last_material_change": True,
            "threats": ["An incomplete record could bypass a readiness control."],
            "mitigations": ["Fail-closed checks and adversarial tests."],
            "evidence_path": "fixture",
        }
        cases = ("stale", "missing_threats")
        for case in cases:
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["threat_model"] = json.loads(json.dumps(valid))
                if case == "stale":
                    task["threat_model"][
                        "reviewed_after_last_material_change"
                    ] = False
                else:
                    task["threat_model"]["threats"] = []

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "threat_model"),
                    "DEGS-SEC-001",
                )

    def test_tier2_incomplete_monitoring_and_safe_degradation_is_blocked(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        valid = {
            "applicable": True,
            "status": "VERIFIED",
            "owner": "Taylor",
            "expected_operating_range": ["Controlled gate decisions only."],
            "alert_thresholds": ["Any evidence mismatch."],
            "stop_thresholds": ["Unknown control state or critical warning."],
            "reassessment_triggers": ["Policy or environment drift."],
            "safe_degradation": "Stop without executing and report sanitized gaps.",
            "evidence_path": "fixture",
        }
        cases = ("missing_stop_threshold", "missing_safe_degradation")
        for case in cases:
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["monitoring"] = json.loads(json.dumps(valid))
                if case == "missing_stop_threshold":
                    task["monitoring"]["stop_thresholds"] = []
                else:
                    task["monitoring"]["safe_degradation"] = ""

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "monitoring"),
                    "DEGS-OPS-002",
                )

    def test_tier2_incomplete_consequential_ai_assurance_is_blocked(self):
        base = self.fixture_payload("tier2-complete-pass.json")
        valid = {
            "applicable": True,
            "status": "VERIFIED",
            "consequential": True,
            "intended_uses": ["Evaluate synthetic Tier 2 readiness records."],
            "unsupported_uses": ["Authorize or execute configuration changes."],
            "affected_stakeholders": ["Taylor"],
            "provenance": "The deterministic gate and fixture are identified.",
            "foreseeable_misuse": ["Treating readiness PASS as authority."],
            "operating_bounds": ["Schema-version-1 DEGS task records only."],
            "criteria": {
                category: [
                    {
                        "measure": f"Synthetic {category} criterion",
                        "threshold": "PASS",
                        "evidence_path": "fixture",
                    }
                ]
                for category in ("quality", "safety", "security", "fairness")
            },
            "human_decision_owner": "Taylor",
            "override_path": "Taylor may stop before execution.",
            "stop_path": "BLOCKED or FAIL stops the workflow.",
            "fallback_path": "Return sanitized unmet requirements.",
            "rollback_path": "Restore the verified baseline.",
            "monitoring_and_reassessment_triggers": ["Policy or environment drift."],
            "retirement_condition": "Retire when the policy is superseded.",
            "representative_tests": {
                "status": "PASS",
                "representative": True,
                "adversarial": True,
                "human_handoff": True,
                "evidence_path": "fixture",
            },
            "limitations": ["The fixture does not prove evidence authenticity."],
            "evidence_path": "fixture",
        }
        cases = (
            "missing_stop_path",
            "missing_reassessment_triggers",
            "missing_retirement_condition",
            "wrong_human_owner",
            "missing_adversarial_system_test",
            "missing_fairness_criteria",
            "blank_safety_threshold",
        )
        for case in cases:
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["ai_assurance"] = json.loads(json.dumps(valid))
                if case == "missing_stop_path":
                    task["ai_assurance"]["stop_path"] = ""
                elif case == "missing_reassessment_triggers":
                    task["ai_assurance"]["monitoring_and_reassessment_triggers"] = []
                elif case == "missing_retirement_condition":
                    task["ai_assurance"]["retirement_condition"] = ""
                elif case == "wrong_human_owner":
                    task["ai_assurance"]["human_decision_owner"] = "Agent"
                elif case == "missing_adversarial_system_test":
                    task["ai_assurance"]["representative_tests"][
                        "adversarial"
                    ] = False
                elif case == "missing_fairness_criteria":
                    task["ai_assurance"]["criteria"].pop("fairness")
                else:
                    task["ai_assurance"]["criteria"]["safety"][0][
                        "threshold"
                    ] = ""

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "ai_assurance"),
                    "DEGS-AI-006",
                )

    def test_tier2_author_cannot_be_independent_reviewer(self):
        task = self.fixture_payload("tier2-complete-pass.json")
        task["task_author"] = "SAME_ROLE"
        task["independent_review"].update(
            {
                "reviewer": "SAME_ROLE",
                "open_issues_status": "NONE",
                "retest_status": "PASS",
            }
        )

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "independent_review"),
            "DEGS-VV-007",
        )

    def test_tier2_blank_nested_control_evidence_fails_closed(self):
        cases = (
            ("deterministic_controls", "boundaries", "filesystem_write", "mechanism", "DEGS-SEC-006"),
            ("change_traceability", "links", 0, "tests", "DEGS-CFG-006"),
            ("data_governance", "data_classes", "DEGS-DATA-003"),
            ("threat_model", "threats", "DEGS-SEC-001"),
            ("monitoring", "alert_thresholds", "DEGS-OPS-002"),
            ("ai_assurance", "intended_uses", "DEGS-AI-006"),
        )
        for case in cases:
            field = case[0]
            rule_id = case[-1]
            with self.subTest(field=field):
                task = self.fixture_payload("tier2-complete-pass.json")
                if field == "deterministic_controls":
                    task[field][case[1]][case[2]][case[3]] = "   "
                elif field == "change_traceability":
                    task[field][case[1]][case[2]][case[3]] = [""]
                else:
                    task[field][case[1]] = [""]

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(self.unmet_rule_for_field(payload, field), rule_id)

    def test_tier2_reasoned_non_applicability_is_accepted(self):
        task = self.fixture_payload("tier2-complete-pass.json")
        for field in (
            "data_governance",
            "threat_model",
            "ai_assurance",
            "monitoring",
        ):
            task[field] = {
                "applicable": False,
                "status": "NOT_APPLICABLE",
                "reason": f"Synthetic {field} is outside this bounded fixture.",
            }

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")

    def test_tier2_unmet_controls_report_governing_rule_ids(self):
        task = self.fixture_payload("tier2-complete-pass.json")
        task["backup"] = {"required": True, "status": "MISSING"}
        task["rollback"] = {"required": True, "status": "MISSING"}
        task["risk_analysis"] = {"status": "MISSING"}
        task["tests"]["negative"] = []
        task["tests"]["security"] = []
        task["tests"]["failure_path"] = []
        task["tests"]["end_to_end"] = []
        task["independent_review"] = {"required": True, "status": "MISSING"}
        task["documentation"] = {"status": "MISSING"}

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        expected = {
            "backup": "DEGS-RISK-002",
            "rollback": "DEGS-CFG-004",
            "risk_analysis": "DEGS-RISK-001",
            "tests.negative": "DEGS-VV-003",
            "tests.security": "DEGS-SEC-001",
            "tests.failure_path": "DEGS-VV-004",
            "tests.end_to_end": "DEGS-VV-006",
            "independent_review": "DEGS-VV-007",
            "documentation": "DEGS-CONTEXT-001",
        }
        for field, rule_id in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.unmet_rule_for_field(payload, field), rule_id)

    def test_tier2_informational_rule_list_matches_applicable_controls(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier2-complete-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        rules = payload["applicable_rule_ids"]
        self.assertNotIn("DEGS-RISK-003", rules)
        for rule_id in (
            "DEGS-RISK-001",
            "DEGS-RISK-002",
            "DEGS-CFG-004",
            "DEGS-VV-003",
            "DEGS-SEC-001",
            "DEGS-VV-004",
            "DEGS-VV-006",
            "DEGS-VV-007",
            "DEGS-CONTEXT-001",
        ):
            with self.subTest(rule_id=rule_id):
                self.assertIn(rule_id, rules)

    def test_tier3_without_human_approval_is_blocked(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier3-no-human-approval-blocked.json"
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertTrue(
            any(
                item["field"] == "human_approval"
                for item in payload["unmet_requirements"]
            )
        )

    def test_tier3_agent_self_approval_is_blocked(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier3-agent-self-approval-blocked.json"
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "human_approval"), "DEGS-RISK-003"
        )

    def test_tier3_missing_approver_role_is_blocked(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["human_approval"].pop("approver_role", None)
        task["human_approval"]["approval_mode"] = "OUT_OF_BAND"

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "human_approval"), "DEGS-RISK-003"
        )

    def test_tier3_in_band_approval_record_is_blocked(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["human_approval"]["approver_role"] = "HUMAN"
        task["human_approval"]["approval_mode"] = "IN_BAND"

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "human_approval"), "DEGS-RISK-003"
        )

    def test_tier3_lowercase_approval_status_is_blocked(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["human_approval"]["status"] = "approved"

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(
            self.unmet_rule_for_field(payload, "human_approval"), "DEGS-RISK-003"
        )

    def test_tier3_complete_dry_run_passes_for_readiness_only(self):
        completed, payload = self.run_gate(
            "evaluate", FIXTURES / "tier3-complete-dry-run-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")
        self.assertIn("DEGS-RISK-004", payload["applicable_rule_ids"])

    def test_tier3_hazard_and_residual_risk_controls_fail_closed(self):
        base = self.fixture_payload("tier3-complete-dry-run-pass.json")
        valid = {
            "status": "COMPLETE",
            "hazards": [
                {
                    "hazard_id": "SYNTHETIC-001",
                    "description": "A synthetic control could be bypassed.",
                    "disposition": "MITIGATED",
                    "control": "Fail-closed evaluator and stop path.",
                    "test_status": "PASS",
                    "evidence_path": "fixture",
                }
            ],
            "cross_domain_check": {
                "status": "PASS",
                "evidence_path": "fixture",
            },
            "residual_risk": {
                "status": "NONE",
                "description": "No live action occurs in the synthetic fixture.",
            },
            "evidence_path": "fixture",
        }
        cases = (
            "missing_analysis",
            "agent_acceptance",
            "human_acceptance_without_evidence",
            "failed_cross_domain_check",
        )
        for case in cases:
            with self.subTest(case=case):
                task = json.loads(json.dumps(base))
                task["hazard_analysis"] = json.loads(json.dumps(valid))
                if case == "missing_analysis":
                    task.pop("hazard_analysis")
                elif case == "agent_acceptance":
                    task["hazard_analysis"]["residual_risk"] = {
                        "status": "ACCEPTED",
                        "description": "Synthetic residual risk.",
                        "acceptor": "Taylor",
                        "acceptor_role": "AGENT",
                        "acceptance_mode": "OUT_OF_BAND",
                        "evidence_path": "fixture",
                    }
                elif case == "human_acceptance_without_evidence":
                    task["hazard_analysis"]["residual_risk"] = {
                        "status": "ACCEPTED",
                        "description": "Synthetic residual risk.",
                        "acceptor": "Taylor",
                        "acceptor_role": "HUMAN",
                        "acceptance_mode": "OUT_OF_BAND",
                        "evidence_path": "",
                    }
                else:
                    task["hazard_analysis"]["cross_domain_check"]["status"] = (
                        "FAIL"
                    )

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                self.assertEqual(
                    self.unmet_rule_for_field(payload, "hazard_analysis"),
                    "DEGS-RISK-006",
                )

    def test_tier3_unmet_controls_report_governing_rule_ids(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["human_approval"]["status"] = "MISSING"
        task["independent_review"].pop("kind")
        task["post_action_validation"]["status"] = "MISSING"
        task["dry_run"]["status"] = "MISSING"

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        expected = {
            "human_approval": "DEGS-RISK-003",
            "independent_review": "DEGS-VV-008",
            "post_action_validation": "DEGS-RISK-004",
            "dry_run": "DEGS-VV-008",
        }
        for field, rule_id in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.unmet_rule_for_field(payload, field), rule_id)

    def test_invalid_json_returns_invalid_input_exit_code(self):
        completed, payload = self.run_payload("validate", raw_text="{not-json")

        self.assertEqual(completed.returncode, 4)
        self.assertEqual(payload["decision"], "FAIL")

    def assert_invalid_input(self, completed, payload):
        self.assertEqual(completed.returncode, 4, completed.stderr)
        self.assertEqual(payload["decision"], "FAIL")
        self.assertTrue(payload["unmet_requirements"])
        self.assertEqual(completed.stderr, "")

    def test_duplicate_task_keys_are_rejected_at_every_object_depth(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task.pop("status")
        body = json.dumps(task)[1:]
        cases = {
            "stop_then_complete": '{"status":"BLOCKED","status":"COMPLETE",' + body,
            "complete_then_stop": '{"status":"COMPLETE","status":"BLOCKED",' + body,
            "equal_values": '{"status":"COMPLETE","status":"COMPLETE",' + body,
            "escaped_key": '{"status":"BLOCKED","sta\\u0074us":"COMPLETE",' + body,
            "nested": (
                '{"schema_version":1,"handoff":'
                '{"status":"BLOCKED","status":"COMPLETE"}}'
            ),
            "object_in_array": (
                '{"schema_version":1,"tests":{"positive":'
                '[{"status":"FAIL","status":"PASS"}]}}'
            ),
        }
        for command in ("validate", "evaluate", "explain"):
            for case, text in cases.items():
                with self.subTest(command=command, case=case):
                    completed, payload = self.run_payload(command, raw_text=text)
                    self.assert_invalid_input(completed, payload)
                    self.assertEqual(payload["unmet_requirements"][0]["field"], "input")

    def test_invalid_utf8_returns_structured_failure(self):
        for command in ("validate", "evaluate", "explain"):
            with self.subTest(command=command):
                completed, payload = self.run_payload(
                    command, raw_bytes=b'{"schema_version":1,"title":"\xff"}'
                )
                self.assert_invalid_input(completed, payload)

    def test_nonfinite_json_constants_are_rejected(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task["scope"]["nonfinite_probe"] = "NONFINITE_PLACEHOLDER"
        template = json.dumps(task)
        for token in ("NaN", "Infinity", "-Infinity"):
            raw_text = template.replace('"NONFINITE_PLACEHOLDER"', token)
            for command in ("validate", "evaluate", "explain"):
                with self.subTest(token=token, command=command):
                    completed, payload = self.run_payload(command, raw_text=raw_text)
                    self.assert_invalid_input(completed, payload)

    def test_excessive_state_nesting_returns_structured_failure(self):
        cases = {
            depth: '{"schema_version":1,"state":'
            + "[" * depth + "0" + "]" * depth + "}"
            for depth in (600, 2000)
        }
        for command in ("validate", "evaluate", "explain"):
            for case, text in cases.items():
                with self.subTest(command=command, case=case):
                    completed, payload = self.run_payload(command, raw_text=text)
                    self.assert_invalid_input(completed, payload)

    def test_excessive_nesting_anywhere_returns_structured_failure(self):
        depth = 1050
        raw_text = (
            '{"schema_version":1,"unexpected":'
            + "[" * depth
            + "0"
            + "]" * depth
            + "}"
        )
        for command in ("validate", "evaluate", "explain"):
            with self.subTest(command=command):
                completed, payload = self.run_payload(command, raw_text=raw_text)
                self.assert_invalid_input(completed, payload)

    def test_malformed_control_types_return_schema_failure(self):
        cases = (
            ("tier1-reversible-pass.json", ("authority_lane",)),
            ("tier2-complete-pass.json", ("artifact_identity", "method")),
            ("tier2-complete-pass.json", ("independent_review", "open_issues_status")),
            ("tier3-complete-dry-run-pass.json", ("hazard_analysis", "hazards", 0, "disposition")),
            ("tier1-reversible-pass.json", ("status",)),
        )
        for fixture_name, path in cases:
            for value in ([], {}, None, True, 42, 1.5):
                for command in ("validate", "evaluate", "explain"):
                    with self.subTest(path=path, value=value, command=command):
                        task = self.fixture_payload(fixture_name)
                        if path == ("status",):
                            # A pre-existing workflow block must not hide bad input.
                            task.pop("handoff")
                        parent = task
                        for key in path[:-1]:
                            parent = parent[key]
                        parent[path[-1]] = value
                        completed, payload = self.run_payload(command, payload=task)
                        self.assert_invalid_input(completed, payload)
                        expected = str(path[0])
                        for key in path[1:]:
                            expected += f"[{key}]" if isinstance(key, int) else f".{key}"
                        self.assertIn(
                            expected,
                            {item["field"] for item in payload["unmet_requirements"]},
                        )

    def test_malformed_nested_controls_are_not_hidden_by_earlier_failures(self):
        cases = (
            (
                "tier2-complete-pass.json",
                ("artifact_identity", "method"),
                ("artifact_identity", "status"),
            ),
            (
                "tier2-complete-pass.json",
                ("independent_review", "open_issues_status"),
                ("independent_review", "reviewer_role"),
            ),
            (
                "tier3-complete-dry-run-pass.json",
                ("hazard_analysis", "hazards", 0, "disposition"),
                ("hazard_analysis", "hazards", 0, "description"),
            ),
        )
        for fixture_name, malformed_path, earlier_failure_path in cases:
            for command in ("evaluate", "explain"):
                with self.subTest(path=malformed_path, command=command):
                    task = self.fixture_payload(fixture_name)
                    parent = task
                    for key in malformed_path[:-1]:
                        parent = parent[key]
                    parent[malformed_path[-1]] = []
                    parent = task
                    for key in earlier_failure_path[:-1]:
                        parent = parent[key]
                    parent[earlier_failure_path[-1]] = ""

                    completed, payload = self.run_payload(command, payload=task)

                    self.assert_invalid_input(completed, payload)
                    expected = str(malformed_path[0])
                    for key in malformed_path[1:]:
                        expected += f"[{key}]" if isinstance(key, int) else f".{key}"
                    self.assertIn(
                        expected,
                        {item["field"] for item in payload["unmet_requirements"]},
                    )

    def test_missing_schema_version_returns_invalid_input_exit_code(self):
        completed, payload = self.run_payload("validate", payload={"task_id": "X"})

        self.assertEqual(completed.returncode, 4)
        self.assertEqual(payload["decision"], "FAIL")

    def test_validate_rejects_structurally_incomplete_task(self):
        completed, payload = self.run_payload(
            "validate", payload={"schema_version": 1, "task_id": "DEGS-TASK-X"}
        )

        self.assertEqual(completed.returncode, 4)
        self.assertEqual(payload["decision"], "FAIL")
        self.assertTrue(
            any(item["field"] == "title" for item in payload["unmet_requirements"])
        )

    def test_validate_rejects_schema_incomplete_tier2_task(self):
        task = {
            "schema_version": 1,
            "task_id": "DEGS-TASK-INCOMPLETE-T2",
            "title": "Incomplete Tier 2 record",
            "objective": "Prove validate fails closed against conditional fields.",
            "authority_lane": "TAYLOR_AI_WORKBENCH",
            "risk_tier": "TIER_2",
            "status": "PLANNED",
        }

        completed, payload = self.run_payload("validate", payload=task)

        self.assertEqual(completed.returncode, 4)
        self.assertEqual(payload["decision"], "FAIL")
        missing = {item["field"] for item in payload["unmet_requirements"]}
        self.assertTrue(
            {"task_author", "deterministic_controls", "artifact_identity"}.issubset(
                missing
            )
        )

    def test_validate_attributes_nested_risk_schema_failure_to_risk_rule(self):
        task = self.fixture_payload("tier2-complete-pass.json")
        task["risk_analysis"]["factors"]["data_sensitivity"] = ""

        completed, payload = self.run_payload("validate", payload=task)

        self.assertEqual(completed.returncode, 4, completed.stderr)
        self.assertEqual(payload["decision"], "FAIL")
        self.assertEqual(
            self.unmet_rule_for_field(
                payload, "risk_analysis.factors.data_sensitivity"
            ),
            "DEGS-RISK-001",
        )

    def test_validate_rejects_required_test_evidence_without_path(self):
        cases = {
            "static": "tier1-reversible-pass.json",
            "positive": "tier1-reversible-pass.json",
            "negative": "tier2-complete-pass.json",
            "security": "tier2-complete-pass.json",
            "failure_path": "tier2-complete-pass.json",
            "end_to_end": "tier2-complete-pass.json",
        }
        for category, fixture_name in cases.items():
            for path_case in ("missing", "empty", "whitespace"):
                with self.subTest(category=category, path_case=path_case):
                    task = self.fixture_payload(fixture_name)
                    task["tests"][category] = [{"status": "PASS"}]
                    if path_case == "empty":
                        task["tests"][category][0]["evidence_path"] = ""
                    elif path_case == "whitespace":
                        task["tests"][category][0]["evidence_path"] = "   "

                    completed, payload = self.run_payload("validate", payload=task)

                    self.assertEqual(completed.returncode, 4, completed.stderr)
                    self.assertEqual(payload["decision"], "FAIL")
                    self.assertIn(
                        f"tests.{category}[0].evidence_path",
                        {item["field"] for item in payload["unmet_requirements"]},
                    )

    def test_validate_requires_tier2_and_tier3_verification_and_validation_evidence(self):
        for fixture_name in (
            "tier2-complete-pass.json",
            "tier3-complete-dry-run-pass.json",
        ):
            for field in ("verification", "validation"):
                for case in (
                    "missing",
                    "empty_path",
                    "whitespace_path",
                    "non_passing",
                ):
                    with self.subTest(
                        fixture=fixture_name, field=field, case=case
                    ):
                        task = self.fixture_payload(fixture_name)
                        if case == "missing":
                            task.pop(field)
                        elif case == "empty_path":
                            task[field]["evidence_path"] = ""
                        elif case == "whitespace_path":
                            task[field]["evidence_path"] = "   "
                        else:
                            task[field]["status"] = "FAIL"

                        completed, payload = self.run_payload(
                            "validate", payload=task
                        )

                        self.assertEqual(completed.returncode, 4, completed.stderr)
                        self.assertEqual(payload["decision"], "FAIL")
                        expected_field = {
                            "missing": field,
                            "empty_path": f"{field}.evidence_path",
                            "whitespace_path": f"{field}.evidence_path",
                            "non_passing": f"{field}.status",
                        }[case]
                        self.assertEqual(
                            self.unmet_rule_for_field(payload, expected_field),
                            "DEGS-VV-001",
                        )

    def test_evaluate_blocks_required_test_evidence_with_blank_path(self):
        cases = {
            "static": ("tier1-reversible-pass.json", "DEGS-VV-001"),
            "positive": ("tier1-reversible-pass.json", "DEGS-VV-002"),
            "negative": ("tier2-complete-pass.json", "DEGS-VV-003"),
            "security": ("tier2-complete-pass.json", "DEGS-SEC-001"),
            "failure_path": ("tier2-complete-pass.json", "DEGS-VV-004"),
            "end_to_end": ("tier2-complete-pass.json", "DEGS-VV-006"),
        }
        for category, (fixture_name, rule_id) in cases.items():
            for path_case in ("missing", "empty", "whitespace"):
                with self.subTest(category=category, path_case=path_case):
                    task = self.fixture_payload(fixture_name)
                    task["tests"][category] = [{"status": "PASS"}]
                    if path_case == "empty":
                        task["tests"][category][0]["evidence_path"] = ""
                    elif path_case == "whitespace":
                        task["tests"][category][0]["evidence_path"] = "   "

                    completed, payload = self.run_payload("evaluate", payload=task)

                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertEqual(payload["decision"], "BLOCKED")
                    self.assertEqual(
                        self.unmet_rule_for_field(payload, f"tests.{category}"),
                        rule_id,
                    )

    def test_validate_rejects_unknown_top_level_and_nested_properties(self):
        for case in ("top_level", "nested"):
            with self.subTest(case=case):
                task = self.fixture_payload("tier2-complete-pass.json")
                if case == "top_level":
                    task["unexpected_control"] = True
                    expected_field = "unexpected_control"
                else:
                    task["artifact_identity"]["unexpected_control"] = True
                    expected_field = "artifact_identity.unexpected_control"

                completed, payload = self.run_payload("validate", payload=task)

                self.assertEqual(completed.returncode, 4)
                self.assertEqual(payload["decision"], "FAIL")
                self.assertIn(
                    expected_field,
                    {item["field"] for item in payload["unmet_requirements"]},
                )

    def test_validate_accepts_complete_fixture_structure(self):
        completed, payload = self.run_gate(
            "validate", FIXTURES / "tier1-reversible-pass.json"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")
        self.assertEqual(payload["unmet_requirements"], [])

    def test_validate_accepts_complete_tier2_and_tier3_schema_records(self):
        for fixture_name in (
            "tier2-complete-pass.json",
            "tier3-complete-dry-run-pass.json",
        ):
            with self.subTest(fixture=fixture_name):
                completed, payload = self.run_gate(
                    "validate", FIXTURES / fixture_name
                )

                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(payload["decision"], "PASS")
                self.assertEqual(payload["unmet_requirements"], [])

    def test_validate_accepts_planned_task_template(self):
        completed, payload = self.run_gate("validate", TASK_TEMPLATE)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["decision"], "PASS")
        self.assertEqual(payload["unmet_requirements"], [])

    def test_evaluate_cannot_pass_schema_incomplete_or_unknown_task(self):
        for case in ("missing_core_fields", "unknown_property"):
            with self.subTest(case=case):
                task = self.fixture_payload("tier2-complete-pass.json")
                if case == "missing_core_fields":
                    for field in ("task_id", "title", "status"):
                        task.pop(field)
                else:
                    task["unexpected_control"] = True

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 4)
                self.assertEqual(payload["decision"], "FAIL")
                self.assertNotEqual(payload["unmet_requirements"], [])

    def test_schema_controls_tier3_human_approval_fields(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        approval = schema["$defs"]["humanApproval"]

        self.assertEqual(
            schema["properties"]["human_approval"]["$ref"],
            "#/$defs/humanApproval",
        )
        self.assertEqual(
            approval["properties"]["approver_role"]["enum"], ["HUMAN", "AGENT"]
        )
        self.assertEqual(
            approval["properties"]["approval_mode"]["enum"],
            ["OUT_OF_BAND", "IN_BAND"],
        )
        tier3_constraints = schema["allOf"][0]["then"]["properties"][
            "human_approval"
        ]
        self.assertEqual(
            set(tier3_constraints["required"]),
            {
                "status",
                "approver",
                "approver_role",
                "approval_mode",
                "evidence_path",
            },
        )
        self.assertEqual(
            tier3_constraints["properties"]["status"]["const"], "APPROVED"
        )
        self.assertEqual(
            tier3_constraints["properties"]["approver"]["const"], "Taylor"
        )
        self.assertEqual(
            tier3_constraints["properties"]["approver_role"]["const"], "HUMAN"
        )
        self.assertEqual(
            tier3_constraints["properties"]["approval_mode"]["const"],
            "OUT_OF_BAND",
        )
        self.assertEqual(
            tier3_constraints["properties"]["evidence_path"]["minLength"], 1
        )

    def test_schema_controls_expanded_tier2_and_tier3_evidence(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        tier3_required = set(schema["allOf"][0]["then"]["required"])
        tier2_required = set(schema["allOf"][1]["then"]["required"])

        self.assertEqual(tier3_required, {"human_approval", "hazard_analysis"})
        self.assertTrue(
            {
                "task_author",
                "deterministic_controls",
                "artifact_identity",
                "change_traceability",
                "data_governance",
                "threat_model",
                "ai_assurance",
                "monitoring",
                "independent_review",
            }.issubset(tier2_required)
        )
        hazard = schema["$defs"]["hazardAnalysis"]
        self.assertEqual(hazard["oneOf"][0]["$ref"], "#/$defs/planningControl")
        completed_hazard = hazard["oneOf"][1]
        self.assertEqual(
            set(completed_hazard["required"]),
            {
                "status",
                "hazards",
                "cross_domain_check",
                "residual_risk",
                "evidence_path",
            },
        )
        accepted = completed_hazard["properties"]["residual_risk"]["oneOf"][1]
        self.assertEqual(accepted["properties"]["acceptor"]["const"], "Taylor")
        self.assertEqual(
            accepted["properties"]["acceptor_role"]["const"], "HUMAN"
        )
        self.assertEqual(
            accepted["properties"]["acceptance_mode"]["const"],
            "OUT_OF_BAND",
        )
        self.assertEqual(
            accepted["properties"]["evidence_path"]["minLength"], 1
        )

    def test_all_fixture_rule_ids_exist_in_charter(self):
        charter_rule_ids = set(
            re.findall(r"\bDEGS-[A-Z]+-\d{3}\b", CHARTER.read_text(encoding="utf-8"))
        )

        for fixture_path in sorted(FIXTURES.glob("*.json")):
            task = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture_rule_ids = set(
                re.findall(r"\bDEGS-[A-Z]+-\d{3}\b", json.dumps(task))
            )
            with self.subTest(fixture=fixture_path.name):
                self.assertEqual(fixture_rule_ids - charter_rule_ids, set())

    def test_unsupported_risk_tier_fails_closed(self):
        completed, payload = self.run_payload(
            "evaluate", payload={"schema_version": 1, "risk_tier": "TIER_9"}
        )

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["decision"], "FAIL")

    def test_unknown_risk_tier_fails_closed(self):
        completed, payload = self.run_payload(
            "evaluate", payload={"schema_version": 1, "risk_tier": "UNKNOWN"}
        )

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["decision"], "FAIL")

    def test_missing_authority_lane_blocks(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task.pop("authority_lane")

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertTrue(
            any(
                item["field"] == "authority_lane"
                for item in payload["unmet_requirements"]
            )
        )

    def test_tier3_missing_recovery_validation_blocks(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task.pop("recovery_validation")

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertTrue(any(item["field"] == "recovery_validation" for item in payload["unmet_requirements"]))

    def test_tier3_missing_independent_review_blocks(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task.pop("independent_review")

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertTrue(any(item["field"] == "independent_review" for item in payload["unmet_requirements"]))

    def test_tier3_missing_target_identity_blocks(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task.pop("target_identity")

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertTrue(any(item["field"] == "target_identity" for item in payload["unmet_requirements"]))

    def test_tier3_missing_stop_conditions_blocks(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["stop_conditions"] = []

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertTrue(any(item["field"] == "stop_conditions" for item in payload["unmet_requirements"]))

    def test_secret_like_telemetry_field_is_rejected(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task["telemetry"]["api_key"] = "placeholder"

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 4)
        self.assertEqual(payload["decision"], "FAIL")

    def test_unresolved_critical_warning_blocks_tier3(self):
        task = self.fixture_payload("tier3-complete-dry-run-pass.json")
        task["warnings"] = [
            {"severity": "CRITICAL", "message": "Synthetic critical warning", "resolved": False, "status": "UNRESOLVED"}
        ]

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["decision"], "BLOCKED")

    def test_noncritical_active_warning_blocks_readiness(self):
        task = self.fixture_payload("tier1-reversible-pass.json")
        task["warnings"] = [
            {"severity": "WARNING", "message": "Synthetic non-critical warning", "resolved": False, "status": "UNRESOLVED"}
        ]

        completed, payload = self.run_payload("evaluate", payload=task)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["decision"], "BLOCKED")

    def test_declared_failed_or_blocked_status_stops_an_otherwise_passing_task(self):
        for declared_status, with_warning in (
            ("FAILED", False),
            ("FAILED", True),
            ("BLOCKED", False),
            ("BLOCKED", True),
        ):
            with self.subTest(
                declared_status=declared_status,
                computed_path="BLOCKED" if with_warning else "PASS",
            ):
                task = self.fixture_payload("tier2-complete-pass.json")
                task["status"] = declared_status
                if with_warning:
                    task["warnings"] = [
                        {
                            "severity": "WARNING",
                            "message": "Synthetic non-critical warning",
                            "resolved": False,
                            "status": "UNRESOLVED",
                        }
                    ]

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertEqual(payload["decision"], "BLOCKED")
                field = "warnings" if with_warning else "status"
                self.assertEqual(self.unmet_rule_for_field(payload, field), "DEGS-OPS-001")
                self.assertIn("DEGS-OPS-001", payload["applicable_rule_ids"])

    def test_schema_invalid_record_takes_precedence_over_declared_stop_status(self):
        for declared_status in ("FAILED", "BLOCKED"):
            with self.subTest(declared_status=declared_status):
                task = self.fixture_payload("tier2-complete-pass.json")
                task["status"] = declared_status
                task["unexpected_control"] = True

                completed, payload = self.run_payload("evaluate", payload=task)

                self.assertEqual(completed.returncode, 4, completed.stderr)
                self.assertEqual(payload["decision"], "FAIL")
                self.assertIn(
                    "unexpected_control",
                    {item["field"] for item in payload["unmet_requirements"]},
                )
                self.assertNotIn(
                    "status",
                    {item["field"] for item in payload["unmet_requirements"]},
                )

    def test_explain_includes_applicable_degs_rule_ids(self):
        completed, payload = self.run_gate(
            "explain", FIXTURES / "tier2-complete-pass.json"
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("DEGS-CFG-004", payload["applicable_rule_ids"])
        self.assertIn("DEGS-CFG-004", payload["explanations"])


if __name__ == "__main__":
    unittest.main()
