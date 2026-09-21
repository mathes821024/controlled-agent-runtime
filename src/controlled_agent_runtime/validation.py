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
}
SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    policy_path = root / "policy/examples/refund-demo-policy.json"
    seed_path = root / "demo-seeds/refund-seed-01.json"

    required_paths = (
        root / "README.md",
        root / "LICENSE",
        root / "SECURITY.md",
        root / "CONTRIBUTING.md",
        root / "GOVERNANCE.md",
        root / "policy/policy.schema.json",
        root / "demo-seeds/seed.schema.json",
        policy_path,
        seed_path,
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")

    if errors:
        return errors

    try:
        policy = load_json(policy_path)
        seed = load_json(seed_path)
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
    guards = policy.get("execution_guards", {})
    if guards.get("pre_execution_revalidation") is not True:
        errors.append("pre_execution_revalidation must be true")
    if guards.get("idempotency") is not True:
        errors.append("idempotency must be true")
    if guards.get("real_adapters_enabled") is not False:
        errors.append("real adapters must be disabled at Gate 0")

    if seed.get("data_mode") != "synthetic_only":
        errors.append("Seed-01 must be synthetic_only")
    email = seed.get("proposal", {}).get("merchant_email", "")
    if not email.endswith(".invalid"):
        errors.append("Seed-01 email must use the reserved .invalid domain")
    expected = seed.get("expected", {})
    events = expected.get("required_event_order", [])
    guard_order = ["policy_decided", "state_revalidated", "idempotency_reserved", "mock_adapter_called"]
    try:
        indexes = [events.index(name) for name in guard_order]
        if indexes != sorted(indexes) or len(set(indexes)) != len(indexes):
            errors.append("Seed-01 execution guards are out of order")
    except ValueError as exc:
        errors.append(f"Seed-01 is missing required guard event: {exc}")
    if "real_adapter_called" not in expected.get("forbidden_events", []):
        errors.append("Seed-01 must forbid real_adapter_called")

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
