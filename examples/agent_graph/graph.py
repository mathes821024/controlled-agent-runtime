"""LangGraph stub: understand → draft_proposal → submit_to_car → done.

CAR decides. No side-effect tools. The only HTTP call is Ingress
``POST {CAR_BASE_URL}/api/agent/propose``.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from .llm import get_agent_llm, resolve_agent_llm_mode

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
ENV_BASE_URL = "CAR_BASE_URL"


class AgentState(TypedDict, total=False):
    user_input: str
    proposal: dict[str, Any]
    car_response: dict[str, Any]
    decision: str
    trace_id: str
    scenario: str | None
    client_trace_id: str | None
    source: str
    car_status_code: int
    llm_mode: str


def resolve_base_url(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = str(env.get(ENV_BASE_URL, DEFAULT_BASE_URL) or DEFAULT_BASE_URL).strip()
    return raw.rstrip("/") or DEFAULT_BASE_URL


def understand(state: AgentState) -> dict[str, Any]:
    """Normalize tracing input. Does not invent a scenario as authority."""
    user_input = str(state.get("user_input") or "").strip()
    scenario = str(state.get("scenario") or "").strip() or None
    return {"user_input": user_input, "scenario": scenario}


def draft_proposal(state: AgentState) -> dict[str, Any]:
    """Stub (or reserved) LLM → structured proposal. No tools."""
    mode = resolve_agent_llm_mode()
    provider = get_agent_llm()
    proposal = provider.draft_proposal(
        state.get("user_input") or "",
        state.get("scenario"),
    )
    return {"proposal": proposal, "llm_mode": mode}


def submit_to_car(state: AgentState) -> dict[str, Any]:
    """The only network hop: Ingress. No adapter or write APIs."""
    base = resolve_base_url()
    payload: dict[str, Any] = {
        "source": state.get("source") or "langgraph_example",
        "proposal": state.get("proposal") or {},
    }
    user_input = state.get("user_input") or ""
    if user_input:
        payload["user_input"] = user_input
    scenario = state.get("scenario")
    if scenario:
        payload["scenario"] = scenario
    client_trace_id = state.get("client_trace_id")
    if client_trace_id:
        payload["client_trace_id"] = client_trace_id
    response = httpx.post(f"{base}/api/agent/propose", json=payload, timeout=30.0)
    try:
        body = response.json()
    except Exception:
        body = {
            "decision": "denied",
            "outcome": "failed_closed",
            "reason_code": "car_response_not_json",
            "adapter_call_count": 0,
        }
    if not isinstance(body, dict):
        body = {
            "decision": "denied",
            "outcome": "failed_closed",
            "reason_code": "car_response_not_object",
            "adapter_call_count": 0,
        }
    return {"car_response": body, "car_status_code": response.status_code}


def done(state: AgentState) -> dict[str, Any]:
    body = state.get("car_response") or {}
    return {
        "decision": str(body.get("decision") or "denied"),
        "trace_id": str(body.get("car_trace_id") or ""),
    }


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("understand", understand)
    graph.add_node("draft_proposal", draft_proposal)
    graph.add_node("submit_to_car", submit_to_car)
    graph.add_node("done", done)
    graph.set_entry_point("understand")
    graph.add_edge("understand", "draft_proposal")
    graph.add_edge("draft_proposal", "submit_to_car")
    graph.add_edge("submit_to_car", "done")
    graph.add_edge("done", END)
    return graph.compile()
