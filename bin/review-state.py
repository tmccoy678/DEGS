#!/usr/bin/env python3
"""Build deterministic review state with the Sashiko-derived value operations."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sashiko_derived import (  # noqa: E402
    ReviewState,
    StageConcernsOutput,
    append_stage_dismissed_concerns,
    append_stage_items,
)


REQUEST_SCHEMA = "degs.sashiko-review-request/v1"
RESULT_SCHEMA = "degs.sashiko-review-state/v1"
SASHIKO_COMMIT = "39f6ce95c797bb40023247916a8b16d0f4aaf0da"
MAX_INPUT_BYTES = 1_048_576
MAX_STAGES = 32
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 50_000
MAX_JSON_NUMBER_DIGITS = 4_300
STAGE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class ReviewInputError(Exception):
    pass


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReviewInputError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ReviewInputError(f"non-finite JSON constant: {value}")


def _bounded_integer(token: str) -> int:
    if sum(character.isdigit() for character in token) > MAX_JSON_NUMBER_DIGITS:
        raise ReviewInputError("JSON integer exceeds the digit bound")
    return int(token)


def _bounded_float(token: str) -> float:
    if sum(character.isdigit() for character in token) > MAX_JSON_NUMBER_DIGITS:
        raise ReviewInputError("JSON decimal exceeds the digit bound")
    value = float(token)
    if not math.isfinite(value):
        raise ReviewInputError("JSON decimal is outside the finite float range")
    return value


def _validate_json_tree(value: Any) -> Any:
    stack, nodes = [(value, 0)], 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise ReviewInputError("JSON structure exceeds its bound")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return value


def _load(path: Path) -> Any:
    if path.is_symlink() or not path.is_file():
        raise ReviewInputError("request must be a regular file")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ReviewInputError(f"request cannot be read: {error}") from error
    if len(raw) > MAX_INPUT_BYTES:
        raise ReviewInputError("request exceeds the input bound")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate,
            parse_constant=_reject_constant,
            parse_int=_bounded_integer,
            parse_float=_bounded_float,
        )
    except ReviewInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        raise ReviewInputError(f"invalid JSON request: {error}") from error
    return _validate_json_tree(value)


def _exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewInputError(f"{label} must be an object")
    if set(value) != keys:
        raise ReviewInputError(f"{label} fields differ: {sorted(set(value) ^ keys)}")
    return value


def _validate_request(value: Any) -> list[dict[str, Any]]:
    request = _exact_object(value, {"schema_version", "stage_outputs"}, "request")
    if request["schema_version"] != REQUEST_SCHEMA:
        raise ReviewInputError("unsupported request schema")
    outputs = request["stage_outputs"]
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= MAX_STAGES:
        raise ReviewInputError("stage_outputs must contain 1 through 32 items")
    stages: set[str] = set()
    for index, output in enumerate(outputs):
        stage = _exact_object(
            output,
            {"stage", "concerns", "dismissed_concerns"},
            f"stage_outputs[{index}]",
        )
        if not isinstance(stage["stage"], str) or STAGE_PATTERN.fullmatch(stage["stage"]) is None:
            raise ReviewInputError(f"invalid stage name at stage_outputs[{index}]")
        if stage["stage"] in stages:
            raise ReviewInputError(f"duplicate stage name at stage_outputs[{index}]")
        stages.add(stage["stage"])
        try:
            StageConcernsOutput.from_mapping(stage)
        except ValueError as error:
            raise ReviewInputError(str(error)) from error
    return outputs


def build_review_state(value: Any) -> dict[str, Any]:
    """Aggregate detached, stage-stamped agent reports without semantic claims."""
    outputs = _validate_request(value)
    state = ReviewState()
    for output in outputs:
        parsed = StageConcernsOutput.from_mapping(output)
        append_stage_items(
            state.all_concerns,
            parsed.concerns,
            output["stage"],
            "General",
            "description",
        )
        append_stage_dismissed_concerns(
            state.all_dismissed_concerns,
            parsed.dismissed_concerns,
            output["stage"],
        )
    return {
        "schema_version": RESULT_SCHEMA,
        "sashiko_source_commit": SASHIKO_COMMIT,
        "report_basis": "AGENT_SUPPLIED_REVIEW_VALUES",
        "agent_reported_concern_status": (
            "UNRESOLVED_REPORTED" if state.all_concerns else "NONE_REPORTED"
        ),
        "all_concerns": state.all_concerns,
        "all_dismissed_concerns": state.all_dismissed_concerns,
        "deduplicated_concerns": state.deduplicated_concerns,
        "deduplicated_dismissed_concerns": state.deduplicated_dismissed_concerns,
        "conflict_resolved_concerns": state.conflict_resolved_concerns,
        "findings": state.findings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build review state")
    build.add_argument("request")
    build.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_review_state(_load(Path(args.request)))
    except ReviewInputError as error:
        print(json.dumps({"state": "REJECTED_INPUT", "error": str(error)}, sort_keys=True))
        return 4
    print(
        json.dumps(
            result,
            allow_nan=False,
            indent=2 if args.json else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
