"""LLM provider abstraction for the example graph.

Default is the deterministic stub. ``local`` and ``openai`` are reserved
for a later OpenAI-compatible endpoint and fail closed until implemented.
No model name is locked. Providers draft structured proposals only.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

try:
    from .stub_llm import scenario_to_payload, user_input_to_proposal
except ImportError:  # pragma: no cover - core tests import this file as a script module
    from stub_llm import scenario_to_payload, user_input_to_proposal

ENV_AGENT_LLM = "CAR_AGENT_LLM"
SUPPORTED_MODES = frozenset({"stub", "local", "openai"})


class AgentLlmProvider(Protocol):
    name: str

    def draft_proposal(
        self, user_input: str, scenario: str | None = None
    ) -> dict[str, Any]:
        """Return ALLOWED_HOOK_FIELDS (or the reserved attack fixture)."""


class StubAgentLlm:
    """Deterministic mapper. No HTTP, no weights, no adapter calls."""

    name = "stub"

    def draft_proposal(
        self, user_input: str, scenario: str | None = None
    ) -> dict[str, Any]:
        scenario_name = str(scenario or "").strip() or None
        if scenario_name:
            return dict(scenario_to_payload(scenario_name)["proposal"])
        return user_input_to_proposal(user_input)


class ReservedAgentLlm:
    """Placeholder for ``local`` / ``openai``. Fail closed; no download."""

    def __init__(self, name: str) -> None:
        self.name = name

    def draft_proposal(
        self, user_input: str, scenario: str | None = None
    ) -> dict[str, Any]:
        del user_input, scenario
        raise ValueError(f"reserved_llm_not_implemented:{self.name}")


def resolve_agent_llm_mode(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = str(env.get(ENV_AGENT_LLM, "stub") or "stub").strip().lower() or "stub"
    if raw not in SUPPORTED_MODES:
        raise ValueError(f"unknown_agent_llm:{raw}")
    return raw


def get_agent_llm(
    environ: dict[str, str] | None = None,
) -> AgentLlmProvider:
    mode = resolve_agent_llm_mode(environ)
    if mode == "stub":
        return StubAgentLlm()
    return ReservedAgentLlm(mode)
