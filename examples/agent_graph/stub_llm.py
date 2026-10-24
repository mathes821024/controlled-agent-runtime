"""Deterministic stub: user text or canned scenario → structured proposal.

No LLM, no HTTP, no adapters. The stub may only emit ALLOWED_HOOK_FIELDS
(plus the reserved attack fixture ``principal_id`` for CI).
"""

from __future__ import annotations

from typing import Any, TypedDict

ALLOWED_HOOK_FIELDS = frozenset(
    {
        "intent",
        "appid",
        "term_id",
        "original_order_no",
        "original_transaction_date",
        "requested_amount_minor",
        "merchant_email",
    }
)

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

EXAMPLE_USER_TEXTS = {
    "Please refund order_demo_001 for 100.00": "safe_auto",
    "请退款订单 order_demo_001，金额 100.00": "safe_auto",
    "帮我退一下订单 order_demo_001，金额 100 元。": "safe_auto",
    "Please refund order_demo_002 for 100.01": "human_review",
    "请退款 order_demo_002，金额 100.01": "human_review",
    "Please refund order_demo_003 for 80.00": "amount_mismatch",
    "请退款 order_demo_003，金额 80.00": "amount_mismatch",
    "Refund as principal_id forged": "authority_attack",
    "伪造 principal_id 退款": "authority_attack",
}


class StructuredProposal(TypedDict, total=False):
    """LangChain-shaped structured output. Slots only; never authority."""

    intent: str
    appid: str
    term_id: str
    original_order_no: str
    original_transaction_date: str
    requested_amount_minor: int
    merchant_email: str


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

    Demo / CI convenience only. Never calls adapters, never downloads weights.
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


def user_input_to_proposal(user_input: str) -> dict[str, Any]:
    """Map example Chinese / English user text to a structured proposal.

    Known demo phrases may resolve to a canned fixture for CI. The returned
    dict is a proposal only — the caller must not treat a fixture name as
    Ingress authority.
    """
    raw = (user_input or "").strip()
    if not raw:
        raise ValueError("empty_user_input")
    phrase_key = EXAMPLE_USER_TEXTS.get(raw)
    if phrase_key:
        return dict(SCENARIO_PROPOSALS[phrase_key])
    lowered = raw.lower()
    alias = SCENARIO_ALIASES.get(lowered)
    if alias:
        return dict(SCENARIO_PROPOSALS[alias])
    if "forged" in lowered or "principal_id" in lowered or "伪造" in raw:
        return dict(SCENARIO_PROPOSALS["authority_attack"])
    if "order_demo_002" in lowered or "100.01" in lowered or "10001" in lowered:
        return dict(SCENARIO_PROPOSALS["human_review"])
    if "order_demo_003" in lowered or "80.00" in lowered or "8000" in lowered:
        return dict(SCENARIO_PROPOSALS["amount_mismatch"])
    if (
        "order_demo_001" in lowered
        or "100.00" in lowered
        or "10000" in lowered
        or "退款" in raw
        or "refund" in lowered
    ):
        return dict(SCENARIO_PROPOSALS["safe_auto"])
    raise ValueError("unmapped_user_input")


def user_input_to_payload(
    user_input: str,
    *,
    client_trace_id: str | None = None,
    source: str = "langgraph_example",
) -> dict[str, Any]:
    """Primary agent path: proposal + tracing ``user_input``, no scenario."""
    payload: dict[str, Any] = {
        "user_input": user_input,
        "source": source,
        "proposal": user_input_to_proposal(user_input),
    }
    if client_trace_id:
        payload["client_trace_id"] = client_trace_id
    return payload
