"""Agent propose handler: untrusted proposal in, ReferenceRuntime decides.

This module is route-free. FastAPI wiring belongs in ``app.py`` (later task).
CAR remains HITL / policy / execution authority.
"""

from __future__ import annotations

import copy
from typing import Any, Optional

from pydantic import BaseModel, Field

from controlled_agent_runtime.demo.scenarios import (
    build_seed_for_scenario,
    normalize_scenario,
)
from controlled_agent_runtime.observability import start_trace
from controlled_agent_runtime.proposal_hook import (
    ProposalHookError,
    sanitize_hook_proposal,
)
from controlled_agent_runtime.runtime import ReferenceRuntime

HITL_PATH = "/"


class AgentProposeRequest(BaseModel):
    """Ingress body. ``proposal`` is non-authoritative and optional."""

    scenario: str = Field(..., min_length=1, max_length=64)
    proposal: Optional[dict[str, Any]] = None
    source: Optional[str] = Field(default=None, max_length=128)
    client_trace_id: Optional[str] = Field(default=None, max_length=128)


def map_ingress_decision(outcome: str) -> str:
    """Map runtime ``outcome`` to the ingress ``decision`` contract."""
    if outcome in {"executed", "idempotent_replay"}:
        return "executed"
    if outcome == "needs_review":
        return "needs_review"
    if outcome == "needs_input":
        return "clarify"
    if outcome in {"denied", "failed_closed"}:
        return "denied"
    return "denied"


def _fail_closed(
    handle: Any,
    *,
    scenario: str,
    reason_code: str,
) -> dict[str, Any]:
    handle.span(
        "car.decision",
        decision="denied",
        outcome="failed_closed",
        reason_code=reason_code,
    )
    return {
        "scenario": scenario,
        "decision": "denied",
        "reason_code": reason_code,
        "evidence_summary": {
            "summary": "fail closed before runtime",
            "reason_code": reason_code,
            "event_names": [],
        },
        "hitl_url": None,
        "car_trace_id": handle.end(decision="denied"),
        "outcome": "failed_closed",
        "adapter_call_count": 0,
    }


def handle_agent_propose(body: AgentProposeRequest) -> dict[str, Any]:
    """Sanitize an optional proposal, then let ReferenceRuntime decide.

    Unknown scenario or ``ProposalHookError`` fail closed without calling the
    runtime (``adapter_call_count=0``). Returns a dict the route can wrap.
    """
    from controlled_agent_runtime.demo.app import serialize_result

    handle = start_trace(
        "car.propose",
        client_trace_id=body.client_trace_id,
        metadata={"source": body.source, "scenario": body.scenario},
    )
    try:
        try:
            canonical = normalize_scenario(body.scenario)
        except KeyError:
            return _fail_closed(
                handle,
                scenario=body.scenario,
                reason_code="unknown_scenario",
            )

        sanitized: dict[str, Any] | None = None
        if body.proposal is not None:
            try:
                sanitized = sanitize_hook_proposal(body.proposal)
            except ProposalHookError as exc:
                return _fail_closed(
                    handle,
                    scenario=canonical,
                    reason_code=exc.reason_code,
                )

        handle.span(
            "car.propose",
            scenario=canonical,
            source=body.source,
            proposal_present=body.proposal is not None,
        )

        seed = build_seed_for_scenario(canonical)
        if sanitized is not None:
            seed = copy.deepcopy(seed)
            seed["proposal"] = sanitized

        try:
            result = ReferenceRuntime().run_seed(seed)
        except Exception as exc:  # noqa: BLE001
            return _fail_closed(
                handle,
                scenario=canonical,
                reason_code=f"runtime_exception:{type(exc).__name__}",
            )

        serialized = serialize_result(canonical, result)
        decision = map_ingress_decision(result.outcome.value)
        evidence = serialized.get("evidence") or []
        event_names = [
            item.get("name", "")
            for item in evidence
            if isinstance(item, dict)
        ]
        serialized["decision"] = decision
        serialized["evidence_summary"] = {
            "summary": serialized.get("summary") or "",
            "reason_code": result.reason_code,
            "event_names": event_names,
        }
        serialized["hitl_url"] = HITL_PATH if decision == "needs_review" else None
        handle.span(
            "car.decision",
            decision=decision,
            outcome=result.outcome.value,
            reason_code=result.reason_code,
        )
        if result.adapter_call_count > 0:
            handle.span("car.adapter", adapter_call_count=result.adapter_call_count)
        serialized["car_trace_id"] = handle.end(decision=decision)
        return serialized
    except Exception as exc:  # noqa: BLE001
        return _fail_closed(
            handle,
            scenario=body.scenario,
            reason_code=f"ingress_exception:{type(exc).__name__}",
        )
