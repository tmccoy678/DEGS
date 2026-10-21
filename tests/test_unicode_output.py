"""Unicode input rejection and readable output through the public CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "bin" / "engineering-gate.py"
COMMANDS = ("validate", "evaluate", "explain")


class UnicodeOutputTests(unittest.TestCase):
    def fixture(self):
        return json.loads((ROOT / "fixtures/tier1-reversible-pass.json").read_text())

    def run_gate(self, task, command, json_output, stdout_encoding=None, ensure_ascii=True):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(json.dumps(task, ensure_ascii=ensure_ascii), encoding="utf-8")
            args = [sys.executable, "-B", str(GATE), command, str(path)]
            if json_output:
                args.append("--json")
            env = os.environ.copy()
            if stdout_encoding:
                env["PYTHONIOENCODING"] = stdout_encoding
            completed = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", env=env,
                check=False, timeout=5,
            )
        self.assertEqual(completed.stderr, "")
        self.assertTrue(completed.stdout)
        return completed

    def test_unpaired_surrogates_rejected_in_every_input_location(self):
        for location in ("evidence_path", "nested_value", "nested_key", "unknown_key", "warning_message", "schema_version"):
            for surrogate in ("\ud800", "\udfff", "\ud800x\udc00", "\udc00\ud800"):
                task = self.fixture()
                if location == "evidence_path":
                    task["tests"]["static"][0]["evidence_path"] = surrogate
                elif location == "nested_value":
                    task["scope"]["unconsumed"] = [{"nested": surrogate}]
                elif location == "nested_key":
                    task["scope"]["unconsumed"] = [{surrogate: "unused"}]
                elif location == "unknown_key":
                    task[surrogate] = "unused"
                elif location == "warning_message":
                    task["warnings"] = [{
                        "severity": "CRITICAL", "status": "UNRESOLVED",
                        "resolved": False, "message": surrogate,
                    }]
                else:
                    task["schema_version"] = surrogate
                for command in COMMANDS:
                    for json_output in (False, True):
                        with self.subTest(location=location, surrogate=repr(surrogate), command=command, json_output=json_output):
                            completed = self.run_gate(task, command, json_output)
                            self.assertEqual(completed.returncode, 4)
                            self.assertIn("InputError", completed.stdout)
                            if json_output:
                                payload = json.loads(completed.stdout)
                                self.assertEqual(payload["decision"], "FAIL")
                                self.assertEqual(payload["unmet_requirements"][0]["field"], "input")
                            else:
                                self.assertTrue(completed.stdout.startswith("Decision: FAIL\n"))

    def test_valid_unicode_and_escaped_surrogate_pairs_are_preserved(self):
        evidence = "evidence/café-证据-🙂.json"
        task = self.fixture()
        task["tests"]["static"][0]["evidence_path"] = evidence
        task["scope"]["unconsumed"] = [{"🙂": "valid"}]
        for ensure_ascii in (False, True):
            for command in COMMANDS:
                for json_output in (False, True):
                    with self.subTest(ensure_ascii=ensure_ascii, command=command, json_output=json_output):
                        completed = self.run_gate(task, command, json_output, ensure_ascii=ensure_ascii)
                        self.assertEqual(completed.returncode, 0)
                        if json_output:
                            self.assertIn(evidence, json.loads(completed.stdout)["evidence_paths"])
                            self.assertTrue(completed.stdout.isascii())
                        else:
                            self.assertTrue(completed.stdout.startswith("Decision: PASS\n"))
                            self.assertIn(evidence, completed.stdout)

    def test_supported_unicode_on_ascii_stdout_preserves_decision(self):
        evidence = "evidence/café-🙂.json"
        task = self.fixture()
        task["tests"]["static"][0]["evidence_path"] = evidence
        for command in COMMANDS:
            for json_output in (False, True):
                with self.subTest(command=command, json_output=json_output):
                    completed = self.run_gate(task, command, json_output, stdout_encoding="ascii:strict")
                    self.assertEqual(completed.returncode, 0)
                    self.assertTrue(completed.stdout.isascii())
                    if json_output:
                        self.assertIn(evidence, json.loads(completed.stdout)["evidence_paths"])
                    else:
                        self.assertIn("caf\\xe9-\\U0001f642.json", completed.stdout)

    def test_human_warnings_have_numbered_labeled_lines(self):
        task = self.fixture()
        task["warnings"] = [{"severity": "CRITICAL", "status": "UNRESOLVED", "resolved": False}]
        task["unresolved_items"] = ["Another recorded issue"]
        for command in ("evaluate", "explain"):
            with self.subTest(command=command):
                completed = self.run_gate(task, command, False)
                self.assertEqual(completed.returncode, 2)
                for label in (
                    "Decision: BLOCKED", "Warning state:", "Unresolved count: 2",
                    "Severity: CRITICAL", "Status: UNRESOLVED", "Resolved: false",
                    "1. Source: warnings[0]", "2. Source: unresolved_items[0]",
                    "Message: An unresolved item is recorded in the task input.",
                ):
                    self.assertIn(label, completed.stdout)
                self.assertNotIn("{'", completed.stdout)
                self.assertNotIn("['", completed.stdout)

    def test_json_warning_contract_remains_structured(self):
        task = self.fixture()
        task["unresolved_items"] = ["Another recorded issue"]
        for command in ("evaluate", "explain"):
            with self.subTest(command=command):
                completed = self.run_gate(task, command, True)
                self.assertEqual(completed.returncode, 2)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["warning_state"], {
                    "unresolved_count": 1, "severity": "CRITICAL",
                    "status": "UNRESOLVED", "resolved": False,
                })
                self.assertEqual(payload["warnings"], [{
                    "number": 1, "field": "unresolved_items[0]", "severity": "CRITICAL",
                    "status": "UNRESOLVED", "resolved": False,
                    "message": "An unresolved item is recorded in the task input.",
                }])

    def test_zero_warning_human_summary_is_labeled(self):
        for command in ("evaluate", "explain"):
            with self.subTest(command=command):
                completed = self.run_gate(self.fixture(), command, False)
                self.assertEqual(completed.returncode, 0)
                for label in ("Unresolved count: 0", "Severity: NONE", "Status: RESOLVED", "Resolved: true"):
                    self.assertIn(label, completed.stdout)


if __name__ == "__main__":
    unittest.main()
