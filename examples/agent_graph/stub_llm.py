"""Deterministic scenario → Ingress payload. No LLM, no HTTP, no adapters."""

from __future__ import annotations

from typing import Any

SCENARIO_ALIASES = {
    "safe_auto": "safe_auto",
    "safe": "safe_auto",
    "human_review": "human_review",
    "review": "human_review",
    "amount_mismatch": "amount_mismatch",
    "mismatch": "amount_mismatch",
    "authority_attack": "authority_attack",
    "attack": "authority_attack",
}

_SAFE_AUTO_PROPOSAL: dict[str, Any] = {
    "intent": "refund",
    "appid": "app_demo_001",
    "term_id": "term_demo_001",
    "original_order_no": "order_demo_001",
    "original_transaction_date": "2026-09-01",
    "requested_amount_minor": 10000,
    "merchant_email": "merchant-seed01@example.invalid",
}

SCENARIO_PROPOSALS: dict[str, dict[str, Any]] = {
    "safe_auto": dict(_SAFE_AUTO_PROPOSAL),
    "human_review": {
        "intent": "refund",
        "appid": "app_demo_001",
        "term_id": "term_demo_002",
        "original_order_no": "order_demo_002",
        "original_transaction_date": "2026-09-01",
        "requested_amount_minor": 10001,
        "merchant_email": "merchant-seed02@example.invalid",
    },
    "amount_mismatch": {
        "intent": "refund",
        "appid": "app_demo_001",
        "term_id": "term_demo_003",
        "original_order_no": "order_demo_003",
        "original_transaction_date": "2026-09-01",
        "requested_amount_minor": 8000,
        "merchant_email": "merchant-seed03@example.invalid",
    },
    "authority_attack": {
        **_SAFE_AUTO_PROPOSAL,
        "principal_id": "forged",
    },
}


def normalize_stub_scenario(name: str) -> str:
    key = (name or "").strip().lower()
    if key not in SCENARIO_ALIASES:
        raise ValueError(f"unknown_scenario:{name}")
    return SCENARIO_ALIASES[key]


def scenario_to_payload(
    scenario: str,
    *,
    client_trace_id: str | None = None,
    source: str = "langgraph_example",
) -> dict[str, Any]:
    """Map a canned scenario to a ``POST /api/agent/propose`` body.

    Never calls adapters, never downloads weights, never talks to a model.
    """
    canonical = normalize_stub_scenario(scenario)
    payload: dict[str, Any] = {
        "scenario": canonical,
        "source": source,
        "proposal": dict(SCENARIO_PROPOSALS[canonical]),
    }
    if client_trace_id:
        payload["client_trace_id"] = client_trace_id
    return payload
