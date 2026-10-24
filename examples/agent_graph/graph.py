"""LangGraph stub: draft_proposal → submit_to_car. CAR decides.

No side-effect tools. The only HTTP call is Ingress
``POST {CAR_BASE_URL}/api/agent/propose``.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from .stub_llm import scenario_to_payload

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
ENV_BASE_URL = "CAR_BASE_URL"
ENV_AGENT_LLM = "CAR_AGENT_LLM"
ENV_OPENAI_KEY = "OPENAI_API_KEY"


class AgentState(TypedDict, total=False):
    scenario: str
    client_trace_id: str | None
    source: str
    proposal_payload: dict[str, Any]
    car_response: dict[str, Any]
    car_status_code: int
    llm_mode: str


def resolve_agent_llm_mode(environ: dict[str, str] | None = None) -> str:
    """Default stub. ``openai`` is reserved and still does not download weights."""
    env = os.environ if environ is None else environ
    raw = str(env.get(ENV_AGENT_LLM, "stub") or "stub").strip().lower()
    if raw == "openai" and str(env.get(ENV_OPENAI_KEY, "") or "").strip():
        return "openai"
    return "stub"


def resolve_base_url(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = str(env.get(ENV_BASE_URL, DEFAULT_BASE_URL) or DEFAULT_BASE_URL).strip()
    return raw.rstrip("/") or DEFAULT_BASE_URL


def draft_proposal(state: AgentState) -> dict[str, Any]:
    """Deterministic stub draft. Optional OpenAI flag falls back to stub in v1."""
    mode = resolve_agent_llm_mode()
    # CAR_AGENT_LLM=openai is accepted only as a future hook. v1 extras do not
    # ship a chat client; never download weights; always emit the stub payload.
    del mode
    payload = scenario_to_payload(
        state["scenario"],
        client_trace_id=state.get("client_trace_id"),
        source=state.get("source") or "langgraph_example",
    )
    return {"proposal_payload": payload, "llm_mode": "stub"}


def submit_to_car(state: AgentState) -> dict[str, Any]:
    """The only network hop: Ingress. No adapter or write APIs."""
    base = resolve_base_url()
    payload = state["proposal_payload"]
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


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("draft_proposal", draft_proposal)
    graph.add_node("submit_to_car", submit_to_car)
    graph.set_entry_point("draft_proposal")
    graph.add_edge("draft_proposal", "submit_to_car")
    graph.add_edge("submit_to_car", END)
    return graph.compile()
