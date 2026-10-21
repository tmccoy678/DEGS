"""Readiness decisions for recorded warnings through the public gate CLI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "bin" / "engineering-gate.py"
FIXTURES = (
    "tier0-readonly-pass.json", "tier1-reversible-pass.json",
    "tier2-complete-pass.json", "tier3-complete-dry-run-pass.json",
)


class WarningPolicyTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))

    def run_gate(self, task, command="evaluate"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(json.dumps(task), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, "-B", str(GATE), command, str(path), "--json"],
                capture_output=True, text=True, timeout=5, check=False,
            )
        self.assertEqual(run.stderr, "")
        return run.returncode, json.loads(run.stdout)

    def test_contradictory_resolution_never_passes_at_any_tier(self):
        for fixture in FIXTURES:
            for severity, resolved, status in (
                ("CRITICAL", False, "RESOLVED"),
                ("CRITICAL", True, "UNRESOLVED"),
                ("CRITICAL", True, "RESOLVED"),
                ("NONE", False, "UNRESOLVED"),
            ):
                task = self.fixture(fixture)
                task["warnings"] = [{
                    "severity": severity, "resolved": resolved, "status": status,
                }]
                for command in ("validate", "evaluate", "explain"):
                    with self.subTest(fixture=fixture, warning=task["warnings"], command=command):
                        code, result = self.run_gate(task, command)
                        self.assertEqual((code, result["decision"]), (4, "FAIL"))

    def test_every_active_item_blocks_and_is_numbered_at_every_tier(self):
        for fixture in FIXTURES:
            task = self.fixture(fixture)
            task["warnings"] = [{
                "severity": "INFO", "resolved": False, "status": "UNRESOLVED",
                "message": "Do not echo this supplied detail",
            }]
            task["unresolved_items"] = ["A pending check", {
                "severity": "CRITICAL", "resolved": False, "status": "UNRESOLVED",
            }]
            for command in ("evaluate", "explain"):
                with self.subTest(fixture=fixture, command=command):
                    code, result = self.run_gate(task, command)
                    self.assertEqual((code, result["decision"]), (2, "BLOCKED"))
                    self.assertEqual(result["warning_state"], {
                        "unresolved_count": 3, "severity": "CRITICAL",
                        "status": "UNRESOLVED", "resolved": False,
                    })
                    self.assertEqual([item["number"] for item in result["warnings"]], [1, 2, 3])
                    self.assertEqual([item["field"] for item in result["warnings"]],
                                     ["warnings[0]", "unresolved_items[0]", "unresolved_items[1]"])
                    self.assertNotIn("Do not echo", json.dumps(result))

    def test_supported_closure_and_empty_lists_have_no_unresolved_item_block(self):
        for fixture in FIXTURES:
            for history in ([], [{
                "severity": "NONE", "resolved": True, "status": "RESOLVED",
                "evidence_path": "synthetic-closure.json",
            }]):
                task = self.fixture(fixture)
                task["warnings"] = history
                for command in ("evaluate", "explain"):
                    with self.subTest(fixture=fixture, history=history, command=command):
                        code, result = self.run_gate(task, command)
                        self.assertEqual((code, result["decision"]), (0, "PASS"))
                        self.assertEqual(result["warnings"], [])
                        self.assertEqual(result["warning_state"], {
                            "unresolved_count": 0, "severity": "NONE",
                            "status": "RESOLVED", "resolved": True,
                        })
                        if history:
                            self.assertIn("synthetic-closure.json", result["evidence_paths"])

    def test_zero_count_does_not_override_other_unmet_controls(self):
        task = self.fixture("tier2-complete-pass.json")
        task["rollback"] = {"required": True, "status": "MISSING"}
        code, result = self.run_gate(task)
        self.assertEqual((code, result["decision"]), (2, "BLOCKED"))
        self.assertEqual(result["warning_state"]["unresolved_count"], 0)

    def test_malformed_records_and_unsubstantiated_closure_are_rejected(self):
        active = {"severity": "CRITICAL", "resolved": False, "status": "UNRESOLVED"}
        malformed = [None, False, 0, [], {}, " "]
        for key, value in (
            ("severity", "CRITICAL "), ("severity", "critical"),
            ("status", "RESOLVED "), ("status", "resolved"),
            ("resolved", "false"), ("resolved", 0),
        ):
            malformed.append(dict(active, **{key: value}))
        for key in active:
            malformed.append({k: v for k, v in active.items() if k != key})
        malformed.extend([
            {"severity": "NONE", "resolved": True, "status": "RESOLVED"},
            {"severity": "NONE", "resolved": True, "status": "RESOLVED", "evidence_path": " "},
        ])
        for field in ("warnings", "unresolved_items"):
            for item in malformed:
                for command in ("validate", "evaluate", "explain"):
                    with self.subTest(field=field, item=item, command=command):
                        task = self.fixture("tier3-complete-dry-run-pass.json")
                        task[field] = [item]
                        code, result = self.run_gate(task, command)
                        self.assertEqual((code, result["decision"]), (4, "FAIL"))

    def test_item_count_cannot_be_supplied_or_zeroed_by_the_caller(self):
        for value in (0, False, "0", None, {"count": 0}):
            task = self.fixture("tier2-complete-pass.json")
            task["unresolved_items"] = value
            code, result = self.run_gate(task)
            self.assertEqual((code, result["decision"]), (4, "FAIL"))
        for field in ("unresolved_count", "warning_state"):
            task = self.fixture("tier2-complete-pass.json")
            task[field] = 0
            code, result = self.run_gate(task)
            self.assertEqual((code, result["decision"]), (4, "FAIL"))

    def test_unresolved_list_cannot_contain_a_resolved_record(self):
        task = self.fixture("tier2-complete-pass.json")
        task["unresolved_items"] = [{
            "severity": "NONE", "resolved": True, "status": "RESOLVED",
            "evidence_path": "synthetic-closure.json",
        }]
        for command in ("validate", "evaluate", "explain"):
            code, result = self.run_gate(task, command)
            self.assertEqual((code, result["decision"]), (4, "FAIL"))

    def test_malformed_warning_is_not_hidden_by_an_existing_stop(self):
        task = self.fixture("tier2-complete-pass.json")
        task["status"] = "BLOCKED"
        task["rollback"] = {"required": True, "status": "MISSING"}
        task["warnings"] = [{"severity": "CRITICAL ", "resolved": False, "status": "UNRESOLVED"}]
        code, result = self.run_gate(task)
        self.assertEqual((code, result["decision"]), (4, "FAIL"))


if __name__ == "__main__":
    unittest.main()
