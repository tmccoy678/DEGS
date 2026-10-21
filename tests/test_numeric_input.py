"""Exact, bounded numeric input through the task loader and public CLI."""

from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "bin" / "engineering-gate.py"
SPEC = importlib.util.spec_from_file_location("numeric_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
COMMANDS = ("validate", "evaluate", "explain")


class NumericInputTests(unittest.TestCase):
    def raw_fixture(self, field, token):
        task = json.loads((ROOT / "fixtures/tier2-complete-pass.json").read_text())
        if field == "orphan_count":
            task["change_traceability"][field] = "NUMERIC_INPUT_TOKEN"
        elif field == "numeric_probe":
            task["scope"][field] = "NUMERIC_INPUT_TOKEN"
        else:
            task[field] = "NUMERIC_INPUT_TOKEN"
        return json.dumps(task).replace('"NUMERIC_INPUT_TOKEN"', token)

    def load_raw(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(raw, encoding="utf-8")
            return GATE.load_task(path)

    def run_raw(self, command, raw, json_output):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(raw, encoding="utf-8")
            args = [sys.executable, str(GATE_PATH), command, str(path)]
            if json_output:
                args.append("--json")
            completed = subprocess.run(args, capture_output=True, text=True, check=False)
        self.assertEqual(completed.stderr, "")
        self.assertTrue(completed.stdout)
        if json_output:
            payload = json.loads(completed.stdout)
            decision = payload["decision"]
        else:
            decision = completed.stdout.splitlines()[0].removeprefix("Decision: ")
        return completed, decision

    def test_nonunit_schema_version_never_rounds_to_one(self):
        for command in COMMANDS:
            for json_output in (False, True):
                with self.subTest(command=command, json_output=json_output):
                    completed, decision = self.run_raw(
                        command, self.raw_fixture("schema_version", "1.0000000000000001"), json_output
                    )
                    self.assertEqual(completed.returncode, 4)
                    self.assertEqual(decision, "FAIL")

    def test_nonzero_orphan_count_never_underflows_to_zero(self):
        for command in COMMANDS:
            for json_output in (False, True):
                with self.subTest(command=command, json_output=json_output):
                    completed, decision = self.run_raw(
                        command, self.raw_fixture("orphan_count", "1e-4000"), json_output
                    )
                    self.assertIn(completed.returncode, (2, 4))
                    self.assertIn(decision, ("BLOCKED", "FAIL"))

    def test_equivalent_supported_constants_still_pass(self):
        for field, tokens in (
            ("schema_version", ("1", "1.0", "1e0", "10e-1")),
            ("orphan_count", ("0", "-0", "0.0", "0e10000")),
        ):
            for token in tokens:
                for command in COMMANDS:
                    with self.subTest(field=field, token=token, command=command):
                        completed, decision = self.run_raw(command, self.raw_fixture(field, token), True)
                        self.assertEqual(completed.returncode, 0)
                        self.assertEqual(decision, "PASS")

    def test_loader_preserves_decimal_values_without_float_intermediate(self):
        tokens = ("0.1", "1.0000000000000001", "1e-4000", "1e4000", "9007199254740993.1")
        for token in tokens:
            with self.subTest(token=token):
                task, error = self.load_raw('{"schema_version": 1, "value": ' + token + '}')
                self.assertIsNone(error)
                self.assertIsInstance(task["value"], Decimal)
                self.assertEqual(task["value"], Decimal(token))
                self.assertTrue(task["value"].is_finite())
        self.assertNotEqual(Decimal("1e-4000"), 0)

    def test_unsupported_representations_fail_before_evaluation(self):
        tokens = (
            "7" * 4301,
            "0." + "7" * 4300,
            "1e10001",
            "1e-10001",
            "1e" + "0" * 4300,
            "NaN", "Infinity", "-Infinity",
        )
        for token in tokens:
            with self.subTest(token=token[:30], length=len(token), seam="loader"):
                task, error = self.load_raw('{"schema_version": 1, "value": ' + token + '}')
                self.assertIsNone(task)
                self.assertIsNotNone(error)
            for command in COMMANDS:
                with self.subTest(token=token[:30], length=len(token), command=command):
                    completed, decision = self.run_raw(command, self.raw_fixture("numeric_probe", token), True)
                    self.assertEqual(completed.returncode, 4)
                    self.assertEqual(decision, "FAIL")

    def test_supported_numeric_budget_boundaries_and_zero_padded_exponents(self):
        for token in ("7" * 4300, "0." + "7" * 4299, "1e10000", "1e-10000", "1e000001"):
            with self.subTest(prefix=token[:30], length=len(token)):
                task, error = self.load_raw('{"schema_version": 1, "value": ' + token + '}')
                self.assertIsNone(error)
                self.assertEqual(task["value"], Decimal(token))

    @unittest.skipUnless(hasattr(sys, "set_int_max_str_digits"), "Interpreter has no integer digit limit")
    def test_active_interpreter_integer_limit_is_preserved(self):
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            task, error = self.load_raw('{"schema_version": 1, "value": ' + "7" * 641 + '}')
            self.assertIsNone(task)
            self.assertIsNotNone(error)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_decimal_constants_keep_booleans_distinct(self):
        for token, expected in (("1", True), ("1.0", True), ("1.0000000000000001", False), ("true", False)):
            task, error = self.load_raw('{"schema_version": 1, "value": ' + token + '}')
            self.assertIsNone(error)
            for keyword in ("const", "enum"):
                schema = {keyword: [1] if keyword == "enum" else 1}
                with self.subTest(token=token, keyword=keyword):
                    self.assertEqual(not GATE.json_schema_errors(task["value"], schema, schema), expected)

    def test_invalid_numeric_identifiers_return_diagnostics_in_both_formats(self):
        for field in ("risk_tier", "authority_lane"):
            for token in ("1.0000000000000001", '[1.0000000000000001]', '{"nested": 1.0000000000000001}'):
                for command in COMMANDS:
                    for json_output in (False, True):
                        with self.subTest(field=field, token=token, command=command, json_output=json_output):
                            completed, decision = self.run_raw(command, self.raw_fixture(field, token), json_output)
                            self.assertIn(completed.returncode, (3, 4))
                            self.assertEqual(decision, "FAIL")


if __name__ == "__main__":
    unittest.main()
