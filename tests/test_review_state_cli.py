#!/usr/bin/env python3
"""Public-seam tests for the Sashiko-derived review-state adapter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "review-state.py"


class ReviewStateCliTests(unittest.TestCase):
    def run_cli(self, payload: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return subprocess.run(
                [sys.executable, "-B", str(CLI), "build", str(request), "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

    def test_build_stamps_and_preserves_review_items(self) -> None:
        concern = {
            "id": "C-001",
            "type": "Correctness",
            "description": "A boundary remains unverified.",
            "reasoning": "Evidence did not cover the boundary.",
            "locations": [],
        }
        dismissed = {
            "id": "D-001",
            "description": "A candidate issue was disproved.",
            "reasoning": "The exact branch prevents it.",
            "locations": [],
        }
        completed = self.run_cli(
            {
                "schema_version": "degs.sashiko-review-request/v1",
                "stage_outputs": [
                    {
                        "stage": "review",
                        "concerns": [concern],
                        "dismissed_concerns": [dismissed],
                    }
                ],
            }
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(
            result["agent_reported_concern_status"],
            "UNRESOLVED_REPORTED",
        )
        self.assertEqual(result["report_basis"], "AGENT_SUPPLIED_REVIEW_VALUES")
        self.assertEqual(result["all_concerns"], [{**concern, "stage": "review"}])
        self.assertEqual(
            result["all_dismissed_concerns"],
            [{**dismissed, "stage": "review"}],
        )
        self.assertEqual(result["deduplicated_concerns"], [])
        self.assertEqual(result["conflict_resolved_concerns"], [])
        self.assertEqual(result["findings"], [])

    def test_empty_review_reports_no_agent_concern_without_claiming_clean(self) -> None:
        completed = self.run_cli(
            {
                "schema_version": "degs.sashiko-review-request/v1",
                "stage_outputs": [
                    {
                        "stage": "review",
                        "concerns": [],
                        "dismissed_concerns": [],
                    }
                ],
            }
        )
        self.assertEqual(completed.returncode, 0)
        result = json.loads(completed.stdout)
        self.assertEqual(result["agent_reported_concern_status"], "NONE_REPORTED")
        self.assertNotIn("decision", result)
        self.assertEqual(result["all_concerns"], [])
        self.assertEqual(result["all_dismissed_concerns"], [])

    def test_unknown_request_field_fails_closed(self) -> None:
        completed = self.run_cli(
            {
                "schema_version": "degs.sashiko-review-request/v1",
                "stage_outputs": [],
                "promotion": "APPROVED",
            }
        )
        self.assertEqual(completed.returncode, 4)
        result = json.loads(completed.stdout)
        self.assertEqual(result["state"], "REJECTED_INPUT")

    def test_nonfinite_nested_value_fails_closed(self) -> None:
        payload = {
            "schema_version": "degs.sashiko-review-request/v1",
            "stage_outputs": [
                {
                    "stage": "review",
                    "concerns": [{"value": float("nan")}],
                    "dismissed_concerns": [],
                }
            ],
        }
        completed = self.run_cli(payload)
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(json.loads(completed.stdout)["state"], "REJECTED_INPUT")

    def test_deep_nested_value_fails_without_traceback(self) -> None:
        value: object = 0
        for _ in range(80):
            value = [value]
        completed = self.run_cli(
            {
                "schema_version": "degs.sashiko-review-request/v1",
                "stage_outputs": [
                    {
                        "stage": "review",
                        "concerns": [value],
                        "dismissed_concerns": [],
                    }
                ],
            }
        )
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(json.loads(completed.stdout)["state"], "REJECTED_INPUT")
        self.assertNotIn("Traceback", completed.stderr)

    def test_duplicate_stage_name_fails_closed(self) -> None:
        output = {
            "stage": "review",
            "concerns": [],
            "dismissed_concerns": [],
        }
        completed = self.run_cli(
            {
                "schema_version": "degs.sashiko-review-request/v1",
                "stage_outputs": [output, output],
            }
        )
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(json.loads(completed.stdout)["state"], "REJECTED_INPUT")


if __name__ == "__main__":
    unittest.main()
