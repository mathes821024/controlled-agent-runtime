"""Dependency-free repository contract checks for Gate 0 artifacts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROTECTED_FIELDS = {
    "principal_id",
    "tenant_id",
    "resource_ref",
    "authorized_by",
    "approval_status",
    "idempotency_key",
    "execution_token",
    "adapter_result",
    "original_amount_minor",
    "refund_amount_minor",
    "respCode",
}
SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)
HITL_THRESHOLD_EXCLUSIVE_MINOR = 10000
REQUIRED_PROPOSAL_FIELDS = {
    "intent",
    "appid",
    "term_id",
    "original_order_no",
    "original_transaction_date",
}
EXECUTION_EVENTS = {
    "mock_adapter_called",
    "real_adapter_called",
    "refund_succeeded",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _validate_money_contract(policy: dict[str, Any], errors: list[str]) -> None:
    money = policy.get("money")
    if not isinstance(money, dict):
        errors.append("policy must declare money contract")
        return
    if money.get("currency") != "CNY":
        errors.append("money.currency must be CNY")
    if money.get("representation") != "integer_minor_units":
        errors.append("money.representation must be integer_minor_units")
    if money.get("minor_units_per_major") != 100:
        errors.append("money.minor_units_per_major must be 100")
    if money.get("hitl_threshold_exclusive_minor") != HITL_THRESHOLD_EXCLUSIVE_MINOR:
        errors.append("money.hitl_threshold_exclusive_minor must be 10000")
    if money.get("floating_amounts_allowed") is not False:
        errors.append("floating amounts must be forbidden")


def _validate_condition_language(policy: dict[str, Any], errors: list[str]) -> None:
    language = policy.get("condition_language")
    if not isinstance(language, dict):
        errors.append("policy must declare condition_language status")
        return
    if language.get("status") != "NOT_FROZEN":
        errors.append("condition_language.status must be NOT_FROZEN in Gate 0")
    required = {
        "deterministic",
        "side_effect_free",
        "fail_closed",
        "schema_validated",
        "versioned",
    }
    have = set(language.get("evaluator_requirements", []))
    if not required <= have:
        errors.append("condition_language.evaluator_requirements incomplete")


def _validate_refund_business_results(policy: dict[str, Any], errors: list[str]) -> None:
    block = policy.get("refund_business_results")
    if not isinstance(block, dict):
        errors.append("policy must declare refund_business_results")
        return
    if block.get("transport_protocol_business_separated") is not True:
        errors.append("transport/protocol/business layers must stay separated")
    codes = block.get("codes", {})
    expected = {
        "00": "REFUND_SUCCEEDED",
        "12": "ALREADY_REFUNDED",
        "other": "REFUND_FAILED",
    }
    if codes != expected:
        errors.append("refund_business_results.codes mapping is incorrect")


def _validate_hitl_rule(policy: dict[str, Any], errors: list[str]) -> None:
    rules = policy.get("rules", [])
    hitl = next((rule for rule in rules if rule.get("rule_id") == "R-04"), None)
    if hitl is None:
        errors.append("policy missing R-04 HITL threshold rule")
        return
    when = hitl.get("when", {})
    if when.get("proposal.requested_amount_minor_greater_than") != HITL_THRESHOLD_EXCLUSIVE_MINOR:
        errors.append("R-04 must use greater_than 10000 minor units")
    if hitl.get("outcome") != "needs_review":
        errors.append("R-04 outcome must be needs_review")


def _validate_seed_common(path: Path, seed: dict[str, Any], errors: list[str]) -> None:
    label = path.name
    if seed.get("data_mode") != "synthetic_only":
        errors.append(f"{label} must be synthetic_only")
    if seed.get("expectation_kind") != "future_conformance_expectation":
        errors.append(f"{label} must set expectation_kind=future_conformance_expectation")
    proposal = seed.get("proposal", {})
    missing = sorted(REQUIRED_PROPOSAL_FIELDS - set(proposal))
    if missing:
        errors.append(f"{label} missing required proposal fields: {', '.join(missing)}")
    email = proposal.get("merchant_email", "")
    if email and not str(email).endswith(".invalid"):
        errors.append(f"{label} email must use the reserved .invalid domain")
    expected = seed.get("expected", {})
    if "real_adapter_called" not in expected.get("forbidden_events", []):
        errors.append(f"{label} must forbid real_adapter_called")
    amount = proposal.get("requested_amount_minor")
    if not isinstance(amount, int):
        errors.append(f"{label} requested_amount_minor must be an integer minor unit")


def _validate_seed_01(seed: dict[str, Any], errors: list[str]) -> None:
    proposal = seed.get("proposal", {})
    facts = seed.get("tool_fixtures", {}).get("transaction_query_tool", {})
    adapter = seed.get("tool_fixtures", {}).get("mock_refund_adapter", {})
    expected = seed.get("expected", {})
    if proposal.get("requested_amount_minor") != HITL_THRESHOLD_EXCLUSIVE_MINOR:
        errors.append("Seed-01 must use amount_minor=10000 boundary case")
    if facts.get("original_amount_minor") != HITL_THRESHOLD_EXCLUSIVE_MINOR:
        errors.append("Seed-01 authoritative amount must be 10000")
    if facts.get("currency") != "CNY":
        errors.append("Seed-01 authoritative currency must be CNY")
    if adapter.get("respCode") != "00":
        errors.append("Seed-01 mock adapter respCode must be 00")
    if adapter.get("normalized_business_result") != "REFUND_SUCCEEDED":
        errors.append("Seed-01 must normalize respCode 00 to REFUND_SUCCEEDED")
    if expected.get("outcome") != "executed":
        errors.append("Seed-01 future expectation outcome must be executed")
    if expected.get("adapter_call_count") != 1:
        errors.append("Seed-01 adapter_call_count must be 1")
    events = expected.get("required_event_order", [])
    guard_order = [
        "policy_decided",
        "state_revalidated",
        "idempotency_reserved",
        "mock_adapter_called",
    ]
    try:
        indexes = [events.index(name) for name in guard_order]
        if indexes != sorted(indexes) or len(set(indexes)) != len(indexes):
            errors.append("Seed-01 execution guards are out of order")
    except ValueError as exc:
        errors.append(f"Seed-01 is missing required guard event: {exc}")


def _validate_negative_seed(
    label: str,
    seed: dict[str, Any],
    *,
    expected_outcome: str,
    reason_code: str,
    amount_check,
    errors: list[str],
) -> None:
    proposal = seed.get("proposal", {})
    facts = seed.get("tool_fixtures", {}).get("transaction_query_tool", {})
    expected = seed.get("expected", {})
    amount_check(proposal, facts, errors)
    if expected.get("outcome") != expected_outcome:
        errors.append(f"{label} outcome must be {expected_outcome}")
    if expected.get("reason_code") != reason_code:
        errors.append(f"{label} reason_code must be {reason_code}")
    if expected.get("adapter_call_count") != 0:
        errors.append(f"{label} adapter_call_count must be 0")
    forbidden = set(expected.get("forbidden_events", []))
    missing_forbid = sorted(EXECUTION_EVENTS - forbidden)
    if missing_forbid:
        errors.append(f"{label} must forbid execution events: {', '.join(missing_forbid)}")
    events = set(expected.get("required_event_order", []))
    leaked = sorted(events & EXECUTION_EVENTS)
    if leaked:
        errors.append(f"{label} required_event_order must not include {', '.join(leaked)}")


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    policy_path = root / "policy/examples/refund-demo-policy.json"
    seed_paths = {
        "seed-01": root / "demo-seeds/refund-seed-01.json",
        "seed-02": root / "demo-seeds/refund-seed-02.json",
        "seed-03": root / "demo-seeds/refund-seed-03.json",
    }

    required_paths = (
        root / "README.md",
        root / "LICENSE",
        root / "SECURITY.md",
        root / "CONTRIBUTING.md",
        root / "GOVERNANCE.md",
        root / "policy/policy.schema.json",
        root / "demo-seeds/seed.schema.json",
        policy_path,
        *seed_paths.values(),
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")

    if errors:
        return errors

    try:
        policy = load_json(policy_path)
        seeds = {key: load_json(path) for key, path in seed_paths.items()}
        load_json(root / "policy/policy.schema.json")
        load_json(root / "demo-seeds/seed.schema.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if policy.get("default_effect") != "deny":
        errors.append("policy default_effect must be deny")
    if policy.get("data_mode") != "synthetic_only":
        errors.append("Gate 0 example policy must be synthetic_only")
    forbidden = set(policy.get("proposal", {}).get("forbidden_fields", []))
    missing_protected = sorted(PROTECTED_FIELDS - forbidden)
    if missing_protected:
        errors.append(f"policy is missing protected fields: {', '.join(missing_protected)}")
    allowed = set(policy.get("proposal", {}).get("allowed_fields", []))
    missing_allowed = sorted(REQUIRED_PROPOSAL_FIELDS - allowed)
    if missing_allowed:
        errors.append(f"policy allowed_fields missing: {', '.join(missing_allowed)}")
    guards = policy.get("execution_guards", {})
    if guards.get("pre_execution_revalidation") is not True:
        errors.append("pre_execution_revalidation must be true")
    if guards.get("idempotency") is not True:
        errors.append("idempotency must be true")
    if guards.get("real_adapters_enabled") is not False:
        errors.append("real adapters must be disabled at Gate 0")

    _validate_money_contract(policy, errors)
    _validate_condition_language(policy, errors)
    _validate_refund_business_results(policy, errors)
    _validate_hitl_rule(policy, errors)

    order_demo = policy.get("refund_order_no_demo", {})
    if order_demo.get("construction") != "original_order_no + appid":
        errors.append("refund_order_no_demo.construction must remain original_order_no + appid")
    if order_demo.get("status") != "OPEN_QUESTION":
        errors.append("refund_order_no_demo.status must remain OPEN_QUESTION")

    for key, path in seed_paths.items():
        _validate_seed_common(path, seeds[key], errors)

    _validate_seed_01(seeds["seed-01"], errors)

    def seed02_amount(proposal: dict[str, Any], facts: dict[str, Any], bucket: list[str]) -> None:
        amount = proposal.get("requested_amount_minor")
        if not isinstance(amount, int) or amount <= HITL_THRESHOLD_EXCLUSIVE_MINOR:
            bucket.append("Seed-02 requested_amount_minor must be > 10000")
        if facts.get("original_amount_minor") != amount:
            bucket.append("Seed-02 authoritative amount should match proposal for threshold-only case")

    def seed03_amount(proposal: dict[str, Any], facts: dict[str, Any], bucket: list[str]) -> None:
        requested = proposal.get("requested_amount_minor")
        original = facts.get("original_amount_minor")
        if requested == original:
            bucket.append("Seed-03 must keep proposal amount != authoritative original")
        if original != HITL_THRESHOLD_EXCLUSIVE_MINOR:
            bucket.append("Seed-03 authoritative original_amount_minor should stay 10000")

    _validate_negative_seed(
        "Seed-02",
        seeds["seed-02"],
        expected_outcome="needs_review",
        reason_code="demo_amount_threshold",
        amount_check=seed02_amount,
        errors=errors,
    )
    _validate_negative_seed(
        "Seed-03",
        seeds["seed-03"],
        expected_outcome="denied",
        reason_code="full_refund_only",
        amount_check=seed03_amount,
        errors=errors,
    )

    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".json", ".py", ".toml", ".yml", ".yaml", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret pattern in {path.relative_to(root)}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Gate 0 repository contracts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
