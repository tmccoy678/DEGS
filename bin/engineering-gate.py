#!/usr/bin/env python3
"""Evaluate DEGS task records without executing the described work."""

import argparse
from decimal import Decimal, InvalidOperation
import json
import re
import sys
from pathlib import Path


EXIT_CODES = {
    "PASS": 0,
    "PASS_WITH_WARNINGS": 1,
    "BLOCKED": 2,
    "FAIL": 3,
}

SECRET_LIKE_KEYS = {
    "api_key",
    "auth",
    "authorization",
    "credential",
    "credentials",
    "password",
    "private_key",
    "recovery_key",
    "secret",
    "secret_value",
    "token",
}

SUPPORTED_RISK_TIERS = {"TIER_0", "TIER_1", "TIER_2", "TIER_3"}
SUPPORTED_AUTHORITY_LANES = {
    "COMMAND_CENTER",
    "TAYLOR_AI_WORKBENCH",
    "AGENTOPS",
    "TAYLOR",
}

DETERMINISTIC_BOUNDARIES = {
    "filesystem_write",
    "command_execution",
    "network_egress",
    "dependency_sources",
    "secret_access",
    "approval",
}

ARTIFACT_IDENTITY_METHODS = {
    "SHA256",
    "SIGNATURE",
    "COMMIT",
    "RELEASE_DIGEST",
    "EQUIVALENT",
}

AI_CRITERIA_CATEGORIES = {"quality", "safety", "security", "fairness"}

RISK_ANALYSIS_FACTORS = {
    "consequence",
    "reversibility",
    "data_sensitivity",
    "operational_reach",
    "physical_effects",
    "affected_party_impact",
    "ai_socio_technical_risk",
}

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "gate.schema.json"

# Bound conversion work without rounding or underflowing accepted JSON numbers.
# These are input representation limits, not a claim of full JSON Schema support.
MAX_JSON_NUMBER_DIGITS = 4300
MAX_JSON_NUMBER_EXPONENT = 10000

SCHEMA_RULE_BY_FIELD = {
    "objective": "DEGS-MISSION-001",
    "requirements": "DEGS-REQ-002",
    "acceptance_criteria": "DEGS-REQ-002",
    "authority_lane": "DEGS-AI-001",
    "risk_tier": "DEGS-RISK-001",
    "risk_analysis": "DEGS-RISK-001",
    "deterministic_controls": "DEGS-SEC-006",
    "artifact_identity": "DEGS-CFG-005",
    "change_traceability": "DEGS-CFG-006",
    "data_governance": "DEGS-DATA-003",
    "threat_model": "DEGS-SEC-001",
    "ai_assurance": "DEGS-AI-006",
    "monitoring": "DEGS-OPS-002",
    "hazard_analysis": "DEGS-RISK-006",
    "human_approval": "DEGS-RISK-003",
    "independent_review": "DEGS-VV-007",
    "verification": "DEGS-VV-001",
    "validation": "DEGS-VV-001",
    "status": "DEGS-OPS-001",
    "warnings": "DEGS-OPS-001",
    "unresolved_items": "DEGS-OPS-001",
}


class InputError(ValueError):
    """A task input cannot be interpreted unambiguously."""


def unique_object(pairs):
    # Reuse the DEAS adapter's duplicate-name check before any value is lost.
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_nonfinite_constant(value):
    raise InputError(f"nonfinite JSON constant: {value}")


def validate_number_representation(token):
    # The JSON decoder supplies a syntactically valid ASCII number token. Check
    # its written representation before constructing either numeric value.
    if sum(character.isdigit() for character in token) > MAX_JSON_NUMBER_DIGITS:
        raise InputError("JSON number exceeds the supported decimal digit budget.")
    _, separator, exponent = token.lower().partition("e")
    if separator:
        # Strip padding before converting, so an otherwise supported exponent
        # cannot trigger an integer conversion limit merely through leading zeros.
        magnitude = exponent.lstrip("+-").lstrip("0") or "0"
        if (
            len(magnitude) > len(str(MAX_JSON_NUMBER_EXPONENT))
            or int(magnitude) > MAX_JSON_NUMBER_EXPONENT
        ):
            raise InputError("JSON number exceeds the supported exponent budget.")


def parse_exact_integer(token):
    validate_number_representation(token)
    # Keep any tighter active interpreter integer-conversion limit in force.
    return int(token)


def parse_exact_decimal(token):
    validate_number_representation(token)
    try:
        # Decimal(string) preserves every supplied digit independently of the
        # arithmetic context precision; there is no binary float intermediary.
        value = Decimal(token)
    except InvalidOperation as error:
        raise InputError("Unsupported JSON decimal representation.") from error
    if not value.is_finite():
        raise InputError("Nonfinite JSON numbers are not supported.")
    return value


def string_control(record, key):
    # Missing controls retain their rule-specific BLOCKED diagnostics.
    # Present non-string controls must not reach hash-based membership checks.
    value = record.get(key)
    if key in record and not isinstance(value, str):
        raise InputError("A supplied string control has the wrong JSON type.")
    return value


def validate_supplied_string_controls(task):
    string_control(task, "authority_lane")
    string_control(task, "status")

    artifact_identity = task.get("artifact_identity")
    if isinstance(artifact_identity, dict):
        string_control(artifact_identity, "method")

    review = task.get("independent_review")
    if isinstance(review, dict):
        string_control(review, "open_issues_status")

    hazard_analysis = task.get("hazard_analysis")
    if not isinstance(hazard_analysis, dict):
        return
    hazards = hazard_analysis.get("hazards")
    if not isinstance(hazards, list):
        return
    for hazard in hazards:
        if isinstance(hazard, dict):
            string_control(hazard, "disposition")


def nonempty(value):
    if value is None or value is False:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


def nonblank_string(value):
    return isinstance(value, str) and bool(value.strip())


def nonblank_string_list(value):
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonblank_string(item) for item in value)
    )


def scope_valid(value):
    return (
        isinstance(value, dict)
        and nonblank_string(value.get("description"))
        and ("read_only" not in value or isinstance(value["read_only"], bool))
    )


def status_is(value, *allowed):
    if not isinstance(value, dict):
        return False
    status = value.get("status")
    return isinstance(status, str) and status.upper() in set(allowed)


def status_with_evidence_path_is(value, *allowed):
    return (
        isinstance(value, dict)
        and value.get("status") in allowed
        and nonblank_string(value.get("evidence_path"))
    )


def test_category_passes(task, category):
    tests = task.get("tests")
    if not isinstance(tests, dict):
        return False
    evidence = tests.get(category)
    return (
        isinstance(evidence, list)
        and bool(evidence)
        and all(
            status_with_evidence_path_is(item, "PASS")
            for item in evidence
        )
    )


def deterministic_controls_valid(value):
    if not (
        isinstance(value, dict)
        and value.get("status") == "VERIFIED"
        and value.get("enforced_outside_model") is True
        and nonblank_string(value.get("evidence_path"))
        and status_is(value.get("denial_test"), "PASS")
        and nonblank_string(value.get("denial_test", {}).get("evidence_path"))
        and status_is(value.get("post_change_verification"), "PASS")
        and nonblank_string(
            value.get("post_change_verification", {}).get("evidence_path")
        )
    ):
        return False
    boundaries = value.get("boundaries")
    if not isinstance(boundaries, dict) or set(boundaries) != DETERMINISTIC_BOUNDARIES:
        return False
    for boundary in boundaries.values():
        if not isinstance(boundary, dict):
            return False
        if boundary.get("status") == "ENFORCED":
            if not nonblank_string(boundary.get("mechanism")):
                return False
        elif boundary.get("status") == "NOT_APPLICABLE":
            if not nonblank_string(boundary.get("reason")):
                return False
        else:
            return False
    return True


def artifact_identity_valid(value):
    if not isinstance(value, dict):
        return False
    identifiers = [
        value.get("reviewed_identifier"),
        value.get("tested_identifier"),
        value.get("execution_identifier"),
        value.get("handoff_identifier"),
    ]
    freshness = value.get("evidence_freshness")
    return (
        value.get("status") == "VERIFIED"
        and string_control(value, "method") in ARTIFACT_IDENTITY_METHODS
        and nonblank_string(value.get("configuration_version"))
        and nonblank_string(value.get("canonical_path"))
        and all(nonblank_string(identifier) for identifier in identifiers)
        and len(set(identifiers)) == 1
        and value.get("match") is True
        and nonblank_string(value.get("provenance"))
        and isinstance(freshness, dict)
        and freshness.get("status") == "CURRENT"
        and nonblank_string(freshness.get("verified_at"))
        and nonblank_string(freshness.get("basis"))
        and nonblank_string(value.get("evidence_path"))
    )


def risk_analysis_valid(value):
    if not (
        isinstance(value, dict)
        and status_is(value, "PASS", "COMPLETE")
        and nonblank_string(value.get("summary"))
        and nonblank_string(value.get("evidence_path"))
    ):
        return False
    factors = value.get("factors")
    return (
        isinstance(factors, dict)
        and set(factors) == RISK_ANALYSIS_FACTORS
        and all(nonblank_string(factor) for factor in factors.values())
    )


def change_traceability_valid(value):
    if not (
        isinstance(value, dict)
        and value.get("status") == "VERIFIED"
        and value.get("orphan_count") == 0
        and nonblank_string(value.get("evidence_path"))
    ):
        return False
    links = value.get("links")
    if not isinstance(links, list) or not links:
        return False
    return all(
        isinstance(link, dict)
        and nonblank_string(link.get("requirement"))
        and nonblank_string(link.get("artifact"))
        and nonblank_string_list(link.get("tests"))
        and nonblank_string(link.get("evidence_path"))
        for link in links
    )


def explicit_non_applicability(value):
    return (
        isinstance(value, dict)
        and value.get("applicable") is False
        and value.get("status") == "NOT_APPLICABLE"
        and nonblank_string(value.get("reason"))
    )


def data_governance_valid(value):
    if explicit_non_applicability(value):
        return True
    if not (
        isinstance(value, dict)
        and value.get("applicable") is True
        and value.get("status") == "VERIFIED"
        and nonblank_string(value.get("purpose"))
        and nonblank_string(value.get("owner"))
        and nonblank_string_list(value.get("data_classes"))
        and nonblank_string_list(value.get("necessary_fields"))
        and value.get("minimum_necessary") is True
        and nonblank_string(value.get("provenance"))
        and nonblank_string(value.get("authority"))
        and value["authority"].strip().upper() != "UNKNOWN"
        and nonblank_string(value.get("retention"))
        and nonblank_string(value.get("deletion_or_archival_conditions"))
        and nonblank_string(value.get("access_boundary"))
        and nonblank_string(value.get("evidence_path"))
    ):
        return False
    repurposing = value.get("repurposing")
    if not isinstance(repurposing, dict) or not isinstance(
        repurposing.get("planned"), bool
    ):
        return False
    if repurposing.get("planned") is False:
        return True
    return (
        repurposing.get("status") == "AUTHORIZED"
        and nonblank_string(repurposing.get("purpose"))
        and nonblank_string(repurposing.get("authority"))
        and repurposing["authority"].strip().upper() != "UNKNOWN"
        and nonblank_string(repurposing.get("evidence_path"))
    )


def threat_model_valid(value):
    if explicit_non_applicability(value):
        return True
    return (
        isinstance(value, dict)
        and value.get("applicable") is True
        and value.get("status") == "CURRENT"
        and value.get("reviewed_after_last_material_change") is True
        and nonblank_string_list(value.get("threats"))
        and nonblank_string_list(value.get("mitigations"))
        and nonblank_string(value.get("evidence_path"))
    )


def monitoring_valid(value):
    if explicit_non_applicability(value):
        return True
    return (
        isinstance(value, dict)
        and value.get("applicable") is True
        and value.get("status") == "VERIFIED"
        and nonblank_string(value.get("owner"))
        and nonblank_string_list(value.get("expected_operating_range"))
        and nonblank_string_list(value.get("alert_thresholds"))
        and nonblank_string_list(value.get("stop_thresholds"))
        and nonblank_string_list(value.get("reassessment_triggers"))
        and nonblank_string(value.get("safe_degradation"))
        and nonblank_string(value.get("evidence_path"))
    )


def measurable_ai_criteria_valid(value):
    if not isinstance(value, dict) or set(value) != AI_CRITERIA_CATEGORIES:
        return False
    for records in value.values():
        if not isinstance(records, list) or not records:
            return False
        if not all(
            isinstance(record, dict)
            and nonblank_string(record.get("measure"))
            and nonblank_string(record.get("threshold"))
            and nonblank_string(record.get("evidence_path"))
            for record in records
        ):
            return False
    return True


def ai_assurance_valid(value):
    if explicit_non_applicability(value):
        return True
    if not (
        isinstance(value, dict)
        and value.get("applicable") is True
        and value.get("status") == "VERIFIED"
        and value.get("consequential") is True
        and nonblank_string_list(value.get("intended_uses"))
        and nonblank_string_list(value.get("unsupported_uses"))
        and nonblank_string_list(value.get("affected_stakeholders"))
        and nonblank_string(value.get("provenance"))
        and nonblank_string_list(value.get("foreseeable_misuse"))
        and nonblank_string_list(value.get("operating_bounds"))
        and measurable_ai_criteria_valid(value.get("criteria"))
        and value.get("human_decision_owner") == "Taylor"
        and nonblank_string(value.get("override_path"))
        and nonblank_string(value.get("stop_path"))
        and nonblank_string(value.get("fallback_path"))
        and nonblank_string(value.get("rollback_path"))
        and nonblank_string_list(
            value.get("monitoring_and_reassessment_triggers")
        )
        and nonblank_string(value.get("retirement_condition"))
        and nonblank_string_list(value.get("limitations"))
        and nonblank_string(value.get("evidence_path"))
    ):
        return False
    tests = value.get("representative_tests")
    return (
        status_is(tests, "PASS")
        and tests.get("representative") is True
        and tests.get("adversarial") is True
        and tests.get("human_handoff") is True
        and nonblank_string(tests.get("evidence_path"))
    )


def hazard_analysis_valid(value):
    if not (
        isinstance(value, dict)
        and value.get("status") == "COMPLETE"
        and nonblank_string(value.get("evidence_path"))
    ):
        return False
    hazards = value.get("hazards")
    if not isinstance(hazards, list) or not hazards:
        return False
    for hazard in hazards:
        if not (
            isinstance(hazard, dict)
            and nonblank_string(hazard.get("hazard_id"))
            and nonblank_string(hazard.get("description"))
            and string_control(hazard, "disposition") in {"ELIMINATED", "MITIGATED"}
            and nonblank_string(hazard.get("control"))
            and hazard.get("test_status") == "PASS"
            and nonblank_string(hazard.get("evidence_path"))
        ):
            return False
    cross_domain = value.get("cross_domain_check")
    if not (
        status_is(cross_domain, "PASS")
        and nonblank_string(cross_domain.get("evidence_path"))
    ):
        return False
    residual = value.get("residual_risk")
    if not isinstance(residual, dict) or not nonblank_string(
        residual.get("description")
    ):
        return False
    if residual.get("status") == "NONE":
        return True
    return (
        residual.get("status") == "ACCEPTED"
        and residual.get("acceptor") == "Taylor"
        and residual.get("acceptor_role") == "HUMAN"
        and residual.get("acceptance_mode") == "OUT_OF_BAND"
        and nonblank_string(residual.get("evidence_path"))
    )


def independent_review_valid(task):
    review = task.get("independent_review")
    author = task.get("task_author")
    reviewer = review.get("reviewer") if isinstance(review, dict) else None
    return (
        status_is(review, "PASS", "PASS_WITH_WARNINGS")
        and nonblank_string(author)
        and nonblank_string(reviewer)
        and str(author).strip().casefold() != str(reviewer).strip().casefold()
        and nonblank_string(review.get("reviewer_role"))
        and nonblank_string(review.get("evidence_path"))
        and string_control(review, "open_issues_status") in {"NONE", "DISPOSITIONED"}
        and review.get("retest_status") == "PASS"
    )


def add_unmet(unmet, field, rule_id, message):
    unmet.append({"field": field, "rule_id": rule_id, "message": message})


def collect_evidence_paths(value):
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_path" and isinstance(child, str) and child:
                paths.append(child)
            else:
                paths.extend(collect_evidence_paths(child))
    elif isinstance(value, list):
        for child in value:
            paths.extend(collect_evidence_paths(child))
    return list(dict.fromkeys(paths))


def contains_secret_like_field(value):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SECRET_LIKE_KEYS:
                return True
            if contains_secret_like_field(child):
                return True
    elif isinstance(value, list):
        return any(contains_secret_like_field(child) for child in value)
    return False


def result(decision, task, unmet=None, warnings=None, rule_ids=None):
    return {
        "decision": decision,
        "unmet_requirements": unmet or [],
        "warnings": warnings or [],
        "applicable_rule_ids": rule_ids or [],
        "risk_tier": task.get("risk_tier") if isinstance(task.get("risk_tier"), str) else None,
        "authority_lane": task.get("authority_lane") if isinstance(task.get("authority_lane"), str) else None,
        "evidence_paths": collect_evidence_paths(task),
    }


def invalid_result(message, task=None):
    task = task if isinstance(task, dict) else {}
    payload = result(
        "FAIL",
        task,
        unmet=[
            {
                "field": "input",
                "rule_id": "DEGS-REQ-001",
                "message": message,
            }
        ],
        rule_ids=["DEGS-REQ-001"],
    )
    return payload, 4


def validate_unicode_strings(value):
    """Reject unpaired surrogates in every decoded string, including keys."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            # The JSON decoder combines valid escaped high/low pairs into one
            # Unicode scalar. Any remaining surrogate code point is unpaired.
            if any(0xD800 <= ord(character) <= 0xDFFF for character in item):
                raise InputError("Unpaired Unicode surrogates are not supported.")
        elif isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


def load_task(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            task = json.load(
                handle,
                object_pairs_hook=unique_object,
                parse_constant=reject_nonfinite_constant,
                parse_int=parse_exact_integer,
                parse_float=parse_exact_decimal,
            )
        validate_unicode_strings(task)
        if not isinstance(task, dict):
            return None, "Task input must be a JSON object."
        if not json_values_equal(task.get("schema_version"), 1):
            return task, "schema_version must be 1."
        if contains_secret_like_field(task.get("telemetry")) or contains_secret_like_field(task.get("state")):
            return task, "Telemetry or state contains a prohibited secret-like field."
    except (OSError, ValueError, RecursionError) as error:
        # ValueError covers JSON syntax, UTF-8 decoding, duplicate names, and
        # the interpreter's integer-conversion limit at this input boundary.
        return None, f"Task input is not readable valid JSON: {error.__class__.__name__}"
    return task, None


def json_values_equal(left, right):
    # Finite decoded JSON trees: each pair visits one corresponding subtree.
    pending = [(left, right)]
    while pending:
        left, right = pending.pop()
        if isinstance(left, bool) or isinstance(right, bool):
            if type(left) is not type(right) or left != right:
                return False
        elif isinstance(left, list) or isinstance(right, list):
            if not (isinstance(left, list) and isinstance(right, list)):
                return False
            if len(left) != len(right):
                return False
            pending.extend(zip(left, right))
        elif isinstance(left, dict) or isinstance(right, dict):
            if not (isinstance(left, dict) and isinstance(right, dict)):
                return False
            if left.keys() != right.keys():
                return False
            pending.extend((left[key], right[key]) for key in left)
        elif left != right:
            return False
    return True


def json_type_matches(value, expected):
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def child_schema_path(path, child):
    return f"{path}.{child}" if path else str(child)


def resolve_local_schema_ref(reference, root_schema):
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise ValueError("Only local JSON Schema references are supported.")
    node = root_schema
    for raw_token in reference[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise ValueError("JSON Schema reference cannot be resolved.")
        node = node[token]
    return node


def json_schema_errors(value, schema, root_schema, path=""):
    """Evaluate the JSON Schema keywords used by the canonical task schema."""
    if not isinstance(schema, dict):
        return [(path or "input", "Schema node must be an object.")]
    if "$ref" in schema:
        try:
            target = resolve_local_schema_ref(schema["$ref"], root_schema)
        except ValueError as error:
            return [(path or "input", str(error))]
        return json_schema_errors(value, target, root_schema, path)

    errors = []
    for subschema in schema.get("allOf", []):
        errors.extend(json_schema_errors(value, subschema, root_schema, path))

    conditional = schema.get("if")
    if isinstance(conditional, dict) and not json_schema_errors(
        value, conditional, root_schema, path
    ):
        then_schema = schema.get("then")
        if isinstance(then_schema, dict):
            errors.extend(
                json_schema_errors(value, then_schema, root_schema, path)
            )

    branches = schema.get("oneOf")
    if isinstance(branches, list):
        branch_results = [
            json_schema_errors(value, branch, root_schema, path)
            for branch in branches
        ]
        matches = sum(not branch_errors for branch_errors in branch_results)
        if matches == 0:
            errors.extend(min(branch_results, key=len, default=[]))
        elif matches > 1:
            errors.append(
                (path or "input", "Value must match exactly one allowed schema.")
            )

    prohibited = schema.get("not")
    if isinstance(prohibited, dict) and not json_schema_errors(
        value, prohibited, root_schema, path
    ):
        errors.append((path or "input", "Value matches a prohibited schema."))

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not (
            isinstance(expected_types, list)
            and any(json_type_matches(value, item) for item in expected_types)
        ):
            errors.append(
                (
                    path or "input",
                    "Value has the wrong JSON type; expected "
                    + ", ".join(str(item) for item in expected_types),
                )
            )
            return errors

    if "const" in schema and not json_values_equal(value, schema["const"]):
        errors.append((path or "input", "Value does not match the required constant."))
    if "enum" in schema and not any(
        json_values_equal(value, candidate) for candidate in schema["enum"]
    ):
        errors.append((path or "input", "Value is not in the allowed set."))

    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append((path or "input", "String is shorter than the minimum length."))
    if isinstance(value, str) and "pattern" in schema:
        pattern = schema["pattern"]
        try:
            pattern_matches = isinstance(pattern, str) and re.search(pattern, value)
        except re.error:
            pattern_matches = False
        if not pattern_matches:
            errors.append((path or "input", "String does not match the required pattern."))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append((path or "input", "Array has too few items."))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    json_schema_errors(
                        item,
                        item_schema,
                        root_schema,
                        f"{path}[{index}]" if path else f"[{index}]",
                    )
                )
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                errors.append(
                    (
                        child_schema_path(path, required),
                        "Required property is missing.",
                    )
                )
        if isinstance(properties, dict):
            for key, child in value.items():
                if key in properties:
                    errors.extend(
                        json_schema_errors(
                            child,
                            properties[key],
                            root_schema,
                            child_schema_path(path, key),
                        )
                    )
                elif schema.get("additionalProperties") is False:
                    errors.append(
                        (
                            child_schema_path(path, key),
                            "Additional property is not allowed.",
                        )
                    )
    return errors


def schema_rule_for_path(path):
    top_level = path.split(".", 1)[0].split("[", 1)[0]
    return SCHEMA_RULE_BY_FIELD.get(top_level, "DEGS-REQ-001")


def validate_structure(task):
    """Validate the complete canonical task schema with the standard library."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return result(
            "FAIL",
            task,
            unmet=[
                {
                    "field": "input",
                    "rule_id": "DEGS-REQ-001",
                    "message": f"Canonical task schema is unavailable: {error.__class__.__name__}.",
                }
            ],
            rule_ids=["DEGS-REQ-001"],
        )
    raw_errors = json_schema_errors(task, schema, schema)
    unmet = []
    seen = set()
    for field, message in raw_errors:
        identity = (field, message)
        if identity in seen:
            continue
        seen.add(identity)
        add_unmet(unmet, field, schema_rule_for_path(field), message)
    rules = list(dict.fromkeys(item["rule_id"] for item in unmet))
    return result("FAIL" if unmet else "PASS", task, unmet=unmet, rule_ids=rules or ["DEGS-REQ-001"])


def evaluate_tier0(task):
    unmet = []
    scope = task.get("scope")
    read_only = isinstance(scope, dict) and scope.get("read_only") is True
    if not nonblank_string(task.get("objective")):
        unmet.append(
            {
                "field": "objective",
                "rule_id": "DEGS-MISSION-001",
                "message": "Tier 0 requires an objective.",
            }
        )
    if not (scope_valid(scope) and read_only):
        unmet.append(
            {
                "field": "scope.read_only",
                "rule_id": "DEGS-RISK-001",
                "message": "Tier 0 requires an explicit read-only scope.",
            }
        )
    secret_handling = task.get("secret_handling")
    secret_controlled = isinstance(secret_handling, dict) and (
        secret_handling.get("exposure_possible") is False
        or secret_handling.get("controlled") is True
    )
    if not secret_controlled:
        unmet.append(
            {
                "field": "secret_handling",
                "rule_id": "DEGS-SEC-002",
                "message": "Tier 0 must rule out or control secret exposure.",
            }
        )
    if task.get("authority_lane") != "COMMAND_CENTER":
        add_unmet(unmet, "authority_lane", "DEGS-AI-001", "Tier 0 requires the read-mostly Command Center lane.")
    rules = ["DEGS-RISK-001", "DEGS-MISSION-001", "DEGS-SEC-002", "DEGS-AI-001"]
    decision = "BLOCKED" if unmet else "PASS"
    return result(decision, task, unmet=unmet, rule_ids=rules)


def tier1_controls(task):
    unmet = []
    rules = [
        "DEGS-MISSION-001",
        "DEGS-REQ-001",
        "DEGS-REQ-002",
        "DEGS-ARCH-002",
        "DEGS-CFG-001",
        "DEGS-VV-001",
        "DEGS-VV-002",
        "DEGS-OPS-001",
        "DEGS-CONTEXT-001",
        "DEGS-AI-001",
    ]
    if not nonblank_string(task.get("objective")):
        add_unmet(unmet, "objective", "DEGS-MISSION-001", "An objective is required.")
    if not scope_valid(task.get("scope")):
        add_unmet(unmet, "scope", "DEGS-REQ-001", "A bounded scope is required.")
    # This is the task-record evaluation scope: Taylor's human authority may
    # submit Tier 1 or Tier 2 evidence directly. It is intentionally broader
    # than the phase-boundary context-routing scope.
    allowed_lanes = {
        "TIER_1": {"TAYLOR_AI_WORKBENCH", "AGENTOPS", "TAYLOR"},
        "TIER_2": {"TAYLOR_AI_WORKBENCH", "AGENTOPS", "TAYLOR"},
        "TIER_3": {"TAYLOR"},
    }.get(task.get("risk_tier"), set())
    if string_control(task, "authority_lane") not in allowed_lanes:
        add_unmet(unmet, "authority_lane", "DEGS-AI-001", "A supported authority lane appropriate to the risk tier is required.")
    if not nonblank_string_list(task.get("requirements")):
        add_unmet(unmet, "requirements", "DEGS-REQ-002", "Tier 1 requires measurable requirements.")
    if not nonblank_string_list(task.get("acceptance_criteria")):
        add_unmet(unmet, "acceptance_criteria", "DEGS-REQ-002", "Tier 1 requires acceptance criteria.")
    if not status_is(task.get("baseline"), "RECORDED", "PASS", "VERIFIED"):
        add_unmet(unmet, "baseline", "DEGS-CFG-001", "Tier 1 requires a recorded baseline.")
    if not test_category_passes(task, "static"):
        add_unmet(unmet, "tests.static", "DEGS-VV-001", "Tier 1 requires passing static checks.")
    if not test_category_passes(task, "positive"):
        add_unmet(unmet, "tests.positive", "DEGS-VV-002", "Tier 1 requires passing positive tests.")
    rollback = task.get("rollback")
    rollback_is_trivial = (
        isinstance(rollback, dict)
        and rollback.get("required") is False
        and nonblank_string(rollback.get("reason"))
    )
    rollback_is_verified = status_is(rollback, "PASS", "VERIFIED") and nonblank_string(
        rollback.get("procedure")
    )
    if task.get("risk_tier") == "TIER_1" and not (
        rollback_is_trivial or rollback_is_verified
    ):
        add_unmet(unmet, "rollback", "DEGS-ARCH-002", "Tier 1 requires rollback or an explicit reason it is trivial.")
    if not status_is(task.get("handoff"), "PASS", "COMPLETE"):
        add_unmet(unmet, "handoff", "DEGS-CONTEXT-001", "Tier 1 requires a completed handoff.")
    return unmet, rules


def evaluate_tier1(task):
    unmet, rules = tier1_controls(task)
    return result("BLOCKED" if unmet else "PASS", task, unmet=unmet, rule_ids=rules)


def tier2_assurance_controls(task, unmet):
    if not risk_analysis_valid(task.get("risk_analysis")):
        add_unmet(
            unmet,
            "risk_analysis",
            "DEGS-RISK-001",
            "Tier 2 requires an evidenced risk analysis covering consequence, reversibility, data sensitivity, operational reach, physical effects, affected-party impact, and AI or socio-technical risk.",
        )
    if not deterministic_controls_valid(task.get("deterministic_controls")):
        add_unmet(
            unmet,
            "deterministic_controls",
            "DEGS-SEC-006",
            "Tier 2 requires verified deterministic boundaries outside the model, denial tests, and post-change verification; prompt-only or unknown controls fail closed.",
        )
    if not artifact_identity_valid(task.get("artifact_identity")):
        add_unmet(
            unmet,
            "artifact_identity",
            "DEGS-CFG-005",
            "Tier 2 requires the reviewed and execution artifact identities to match using a controlled immutable identity method.",
        )
    if not change_traceability_valid(task.get("change_traceability")):
        add_unmet(
            unmet,
            "change_traceability",
            "DEGS-CFG-006",
            "Tier 2 requires verified requirement-to-artifact-to-test evidence with no orphan links.",
        )
    if not data_governance_valid(task.get("data_governance")):
        add_unmet(
            unmet,
            "data_governance",
            "DEGS-DATA-003",
            "Tier 2 requires explicit data-purpose, minimum-necessary, authority, retention, access, and repurposing evidence, or a reasoned non-applicability record.",
        )
    if not threat_model_valid(task.get("threat_model")):
        add_unmet(
            unmet,
            "threat_model",
            "DEGS-SEC-001",
            "Tier 2 requires a current threat model reviewed after the last material change, or a reasoned non-applicability record.",
        )
    if not monitoring_valid(task.get("monitoring")):
        add_unmet(
            unmet,
            "monitoring",
            "DEGS-OPS-002",
            "Tier 2 requires owned monitoring with operating ranges, alert and stop thresholds, reassessment triggers, and safe degradation, or a reasoned non-applicability record.",
        )
    if not ai_assurance_valid(task.get("ai_assurance")):
        add_unmet(
            unmet,
            "ai_assurance",
            "DEGS-AI-006",
            "Consequential AI work requires intended and unsupported uses, affected stakeholders, human control, representative and adversarial whole-system tests, monitoring triggers, limitations, and retirement criteria; other work requires a reasoned non-applicability record.",
        )


def tier2_test_controls(task, unmet, rules):
    for category, rule_id, label in (
        ("negative", "DEGS-VV-003", "negative tests"),
        ("security", "DEGS-SEC-001", "security tests"),
        ("failure_path", "DEGS-VV-004", "failure-path tests"),
        ("end_to_end", "DEGS-VV-006", "an actual end-to-end user-path test"),
    ):
        if not test_category_passes(task, category):
            add_unmet(unmet, f"tests.{category}", rule_id, f"Tier 2 requires passing {label}.")
            if rule_id not in rules:
                rules.append(rule_id)
    verification = task.get("verification")
    if not status_with_evidence_path_is(verification, "PASS", "VERIFIED"):
        add_unmet(
            unmet,
            "verification",
            "DEGS-VV-001",
            "Tier 2 requires passing verification evidence with a nonblank evidence path.",
        )
    validation = task.get("validation")
    if not status_with_evidence_path_is(validation, "PASS", "VERIFIED"):
        add_unmet(
            unmet,
            "validation",
            "DEGS-VV-001",
            "Tier 2 requires passing validation evidence with a nonblank evidence path.",
        )


def tier2_controls(task):
    unmet, rules = tier1_controls(task)
    rules.extend(
        [
            "DEGS-CFG-002", "DEGS-CFG-003", "DEGS-CFG-004",
            "DEGS-CFG-005", "DEGS-CFG-006", "DEGS-RISK-001",
            "DEGS-RISK-002", "DEGS-VV-003", "DEGS-SEC-001",
            "DEGS-SEC-006", "DEGS-DATA-003", "DEGS-AI-006",
            "DEGS-VV-004", "DEGS-VV-005", "DEGS-VV-006",
            "DEGS-VV-007", "DEGS-OPS-002",
        ]
    )
    rules = list(dict.fromkeys(rules))
    backup = task.get("backup")
    if not (
        status_is(backup, "PASS", "VERIFIED")
        and nonblank_string(backup.get("evidence_path"))
    ):
        add_unmet(unmet, "backup", "DEGS-RISK-002", "Tier 2 requires a verified pre-change backup.")
    rollback = task.get("rollback")
    if not (
        status_is(rollback, "PASS", "VERIFIED")
        and nonblank_string(rollback.get("procedure"))
    ):
        add_unmet(unmet, "rollback", "DEGS-CFG-004", "Tier 2 requires an explicit verified rollback procedure.")
    tier2_assurance_controls(task, unmet)
    tier2_test_controls(task, unmet, rules)
    if not independent_review_valid(task):
        add_unmet(
            unmet,
            "independent_review",
            "DEGS-VV-007",
            "Tier 2 requires a reviewer distinct from the task author, review evidence, open-issue disposition, and passing retest evidence.",
        )
    if not status_is(task.get("documentation"), "PASS", "COMPLETE"):
        add_unmet(unmet, "documentation", "DEGS-CONTEXT-001", "Tier 2 requires canonical documentation.")
    if not status_is(task.get("telemetry"), "SANITIZED", "PASS"):
        add_unmet(unmet, "telemetry", "DEGS-OPS-002", "Tier 2 requires sanitized telemetry or status evidence.")
    return unmet, rules


def evaluate_tier2(task):
    unmet, rules = tier2_controls(task)
    return result("BLOCKED" if unmet else "PASS", task, unmet=unmet, rule_ids=rules)


def unresolved_warning_summaries(task):
    """Number active records after canonical warning-schema validation."""
    summaries = []
    for field in ("warnings", "unresolved_items"):
        for index, item in enumerate(task.get(field, [])):
            if field == "warnings" and item["resolved"] is True:
                continue
            summaries.append({
                "number": len(summaries) + 1,
                "field": f"{field}[{index}]",
                "severity": "CRITICAL",
                "status": "UNRESOLVED",
                "resolved": False,
                "message": "An unresolved item is recorded in the task input.",
            })
    return summaries


def apply_warning_policy(task, payload):
    warnings = unresolved_warning_summaries(task)
    payload["warnings"] = warnings
    payload["warning_state"] = {
        "unresolved_count": len(warnings),
        "severity": "CRITICAL" if warnings else "NONE",
        "status": "UNRESOLVED" if warnings else "RESOLVED",
        "resolved": not warnings,
    }
    if not warnings:
        return payload
    if payload["decision"] != "FAIL":
        payload["decision"] = "BLOCKED"
    for field in ("warnings", "unresolved_items"):
        if not any(item["field"].startswith(field + "[") for item in warnings):
            continue
        add_unmet(
            payload["unmet_requirements"],
            field,
            "DEGS-OPS-001",
            "Every unresolved item is critical and blocks readiness at every risk tier.",
        )
    if "DEGS-OPS-001" not in payload["applicable_rule_ids"]:
        payload["applicable_rule_ids"].append("DEGS-OPS-001")
    return payload


def apply_declared_status_policy(task, payload):
    declared_status = string_control(task, "status")
    if (
        declared_status not in {"FAILED", "BLOCKED"}
        or payload["decision"] not in {"PASS", "PASS_WITH_WARNINGS"}
    ):
        return payload
    payload["decision"] = "BLOCKED"
    add_unmet(
        payload["unmet_requirements"],
        "status",
        "DEGS-OPS-001",
        f"Declared task status {declared_status} is an authoritative stop signal.",
    )
    if "DEGS-OPS-001" not in payload["applicable_rule_ids"]:
        payload["applicable_rule_ids"].append("DEGS-OPS-001")
    return payload


def tier3_containment_controls(task, unmet):
    target = task.get("target_identity")
    if not (
        isinstance(target, dict)
        and target.get("verified") is True
        and nonblank_string(target.get("identifier"))
    ):
        add_unmet(unmet, "target_identity", "DEGS-RISK-004", "Tier 3 requires exact verified target identity.")
    blast_radius = task.get("blast_radius")
    if not (
        isinstance(blast_radius, dict)
        and blast_radius.get("bounded") is True
        and nonblank_string(blast_radius.get("description"))
    ):
        add_unmet(unmet, "blast_radius", "DEGS-RISK-004", "Tier 3 requires a bounded blast radius.")
    if not nonblank_string_list(task.get("stop_conditions")):
        add_unmet(unmet, "stop_conditions", "DEGS-RISK-004", "Tier 3 requires explicit stop conditions.")
    if not status_with_evidence_path_is(task.get("post_action_validation"), "PASS", "VERIFIED"):
        add_unmet(unmet, "post_action_validation", "DEGS-RISK-004", "Tier 3 requires post-action validation evidence.")
    dry_run = task.get("dry_run")
    dry_run_satisfied = isinstance(dry_run, dict) and (
        (
            dry_run.get("applicable") is True
            and dry_run.get("performed") is True
            and status_with_evidence_path_is(dry_run, "PASS")
        )
        or (
            dry_run.get("applicable") is False
            and nonblank_string(dry_run.get("reason"))
        )
    )
    if not dry_run_satisfied:
        add_unmet(unmet, "dry_run", "DEGS-VV-008", "Tier 3 requires a dry run where possible or a documented reason it is not applicable.")


def evaluate_tier3(task):
    unmet, rules = tier2_controls(task)
    rules.extend(
        [
            "DEGS-RISK-003",
            "DEGS-RISK-004",
            "DEGS-RISK-005",
            "DEGS-RISK-006",
            "DEGS-SEC-004",
            "DEGS-VV-006",
            "DEGS-VV-008",
            "DEGS-AI-001",
        ]
    )
    rules = list(dict.fromkeys(rules))
    if task.get("authority_lane") != "TAYLOR":
        add_unmet(unmet, "authority_lane", "DEGS-AI-001", "Tier 3 requires the Taylor authority lane.")
    if not hazard_analysis_valid(task.get("hazard_analysis")):
        add_unmet(
            unmet,
            "hazard_analysis",
            "DEGS-RISK-006",
            "Tier 3 requires a complete tested hazard analysis, a passing cross-domain check, and human-only evidence for any accepted residual risk.",
        )
    approval = task.get("human_approval")
    if not (
        isinstance(approval, dict)
        and approval.get("status") == "APPROVED"
        and approval.get("approver") == "Taylor"
        and approval.get("approver_role") == "HUMAN"
        and approval.get("approval_mode") == "OUT_OF_BAND"
        and nonblank_string(approval.get("evidence_path"))
    ):
        add_unmet(
            unmet,
            "human_approval",
            "DEGS-RISK-003",
            "Tier 3 requires an APPROVED out-of-band HUMAN approval record from Taylor with an evidence path.",
        )
    recovery = task.get("recovery_validation")
    if not (
        status_is(recovery, "PASS", "VERIFIED")
        and recovery.get("independently_verified") is True
        and nonblank_string(recovery.get("evidence_path"))
    ):
        add_unmet(unmet, "recovery_validation", "DEGS-RISK-005", "Tier 3 requires an independently verified recovery path.")
    review = task.get("independent_review")
    if not (
        status_is(review, "PASS", "PASS_WITH_WARNINGS")
        and review.get("kind") == "AUDIT"
        and nonempty(review.get("reviewer_role"))
        and nonempty(review.get("evidence_path"))
    ):
        add_unmet(unmet, "independent_review", "DEGS-VV-008", "Tier 3 requires an independent audit by a separate role or model.")
    tier3_containment_controls(task, unmet)
    return result("BLOCKED" if unmet else "PASS", task, unmet=unmet, rule_ids=rules)


def evaluate(task):
    if task.get("risk_tier") == "TIER_0":
        payload = evaluate_tier0(task)
    elif task.get("risk_tier") == "TIER_1":
        payload = evaluate_tier1(task)
    elif task.get("risk_tier") == "TIER_2":
        payload = evaluate_tier2(task)
    elif task.get("risk_tier") == "TIER_3":
        payload = evaluate_tier3(task)
    else:
        payload = result(
            "FAIL",
            task,
            unmet=[
                {
                    "field": "risk_tier",
                    "rule_id": "DEGS-RISK-001",
                    "message": "Unsupported risk tier; the gate fails closed.",
                }
            ],
            rule_ids=["DEGS-RISK-001"],
        )
    return apply_warning_policy(task, payload)


def render_human(payload):
    lines = [
        f"Decision: {payload['decision']}",
        f"Risk tier: {payload.get('risk_tier')}",
        f"Authority lane: {payload.get('authority_lane')}",
    ]
    if payload["unmet_requirements"]:
        lines.append("Unmet requirements:")
        lines.extend(f"- {item['rule_id']}: {item['message']}" for item in payload["unmet_requirements"])
    warning_state = payload.get("warning_state")
    if warning_state is not None:
        lines.extend([
            "Warning state:",
            f"  Unresolved count: {warning_state['unresolved_count']}",
            f"  Severity: {warning_state['severity']}",
            f"  Status: {warning_state['status']}",
            f"  Resolved: {str(warning_state['resolved']).lower()}",
        ])
    if payload["warnings"]:
        lines.append("Warnings:")
        for item in payload["warnings"]:
            lines.extend([
                f"  {item['number']}. Source: {item['field']}",
                f"     Severity: {item['severity']}",
                f"     Status: {item['status']}",
                f"     Resolved: {str(item['resolved']).lower()}",
                f"     Message: {item['message']}",
            ])
    lines.append("Applicable DEGS rules: " + ", ".join(payload["applicable_rule_ids"]))
    if payload["evidence_paths"]:
        lines.append("Evidence paths:")
        lines.extend(f"- {path}" for path in payload["evidence_paths"])
    return "\n".join(lines)


def parse_args(argv):
    json_output = "--json" in argv
    filtered = [argument for argument in argv if argument != "--json"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "evaluate", "explain"))
    parser.add_argument("task", type=Path)
    parsed = parser.parse_args(filtered)
    parsed.json_output = json_output
    return parsed


def main(argv=None):
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        task, error = load_task(args.task)
        if error:
            payload, exit_code = invalid_result(error, task)
        elif args.command == "validate":
            payload = validate_structure(task)
            exit_code = 4 if payload["decision"] == "FAIL" else 0
        else:
            schema_payload = validate_structure(task)
            try:
                if any(
                    item["field"].split(".", 1)[0].split("[", 1)[0]
                    in {"warnings", "unresolved_items"}
                    for item in schema_payload["unmet_requirements"]
                ):
                    raise InputError("Warning records must have consistent canonical states.")
                validate_supplied_string_controls(task)
                payload = evaluate(task)
                if (
                    schema_payload["decision"] == "FAIL"
                    and payload["decision"] in {"PASS", "PASS_WITH_WARNINGS"}
                ):
                    # Preserve rule-specific BLOCKED diagnostics for intentionally
                    # incomplete negative records, but never allow a schema-invalid
                    # record to receive a passing evaluation.
                    payload = schema_payload
                    exit_code = 4
                else:
                    # Schema-invalid passing records fail before declared task status
                    # can turn them into ordinary workflow stops. Rule-specific
                    # BLOCKED diagnostics for incomplete negative records remain.
                    payload = apply_declared_status_policy(task, payload)
                    exit_code = EXIT_CODES[payload["decision"]]
            except InputError as input_error:
                # Reuse the canonical schema's field and rule diagnostics. Catch
                # only explicit input rejection, not unexpected evaluator defects.
                if schema_payload["decision"] == "FAIL":
                    payload, exit_code = schema_payload, 4
                else:
                    payload, exit_code = invalid_result(str(input_error), task)

        if args.command == "explain" and not error:
            payload["explanations"] = {
                rule_id: "Applicable readiness or completion control."
                for rule_id in payload["applicable_rule_ids"]
            }

        rendered = (
            json.dumps(payload, indent=2, sort_keys=True)
            if args.json_output
            else render_human(payload)
        )
    except RecursionError:
        payload, exit_code = invalid_result(
            "Task input is not readable valid JSON: RecursionError"
        )
        rendered = (
            json.dumps(payload, indent=2, sort_keys=True)
            if args.json_output
            else render_human(payload)
        )

    if not args.json_output:
        # Preserve supported Unicode where the output encoding permits it and
        # visibly escape other characters without changing the gate's decision
        # or reconfiguring the caller's stdout stream. JSON is already ASCII-safe.
        encoding = sys.stdout.encoding or "utf-8"
        rendered = rendered.encode(encoding, errors="backslashreplace").decode(encoding)
    print(rendered)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
