"""LangChain ChatOpenAI-compatible provider (local / openai).

This is the real Agent draft path. CI uses ``CAR_AGENT_LLM=stub`` instead.

LangChain entry points (cited by the review pack):

- ``invoke_structured_proposal`` imports ``ChatOpenAI``
- ``ChatOpenAI.with_structured_output(ProposalDraft)`` emits ALLOWED_HOOK_FIELDS only

Never calls refund / adapter APIs. Never downloads weights. Protected fields
are dropped even if a model tries to emit them.
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, Field

try:
    from .stub_llm import ALLOWED_HOOK_FIELDS, user_input_to_proposal
except ImportError:  # pragma: no cover - core tests import as a script module
    from stub_llm import ALLOWED_HOOK_FIELDS, user_input_to_proposal

ENV_BASE_URL = "CAR_AGENT_LLM_BASE_URL"
ENV_MODEL = "CAR_AGENT_LLM_MODEL"
ENV_API_KEY = "CAR_AGENT_LLM_API_KEY"
ENV_FALLBACK = "CAR_AGENT_LLM_FALLBACK"
DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
LOCAL_PLACEHOLDER_KEY = "not-needed"

SYSTEM_PROMPT = """You extract a synthetic refund proposal for Controlled Agent Runtime.
Return only these slots when the user mentioned them:
intent, appid, term_id, original_order_no, original_transaction_date,
requested_amount_minor, merchant_email.

Rules:
- requested_amount_minor is integer minor units (100.00 CNY or 100 元 => 10000).
- Never emit principal_id, tenant_id, approval, adapter, or other authority fields.
- Do not invent trusted business facts the user did not mention. Leave unknown slots empty.
- You do not approve, refund, or execute anything. CAR decides.
"""


class ProposalDraft(BaseModel):
    """LangChain structured-output schema. Slots only; never authority."""

    intent: str | None = Field(default=None)
    appid: str | None = Field(default=None)
    term_id: str | None = Field(default=None)
    original_order_no: str | None = Field(default=None)
    original_transaction_date: str | None = Field(default=None)
    requested_amount_minor: int | None = Field(default=None)
    merchant_email: str | None = Field(default=None)


def structured_to_proposal(draft: Any) -> dict[str, Any]:
    """Keep ALLOWED_HOOK_FIELDS only. Drop Nones and any leaked extras."""
    if hasattr(draft, "model_dump"):
        raw = draft.model_dump()
    elif isinstance(draft, Mapping):
        raw = dict(draft)
    else:
        raise ValueError("agent_llm_bad_structured_output")
    if not isinstance(raw, Mapping):
        raise ValueError("agent_llm_bad_structured_output")
    proposal = {
        key: raw[key]
        for key in ALLOWED_HOOK_FIELDS
        if key in raw and raw[key] is not None and raw[key] != ""
    }
    return proposal


def resolve_chat_config(
    mode: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Resolve OpenAI-compatible endpoint settings. No model lock-in."""
    import os

    env = os.environ if environ is None else environ
    model = (
        str(env.get(ENV_MODEL, "") or "").strip()
        or str(env.get("OPENAI_MODEL", "") or "").strip()
    )
    if not model:
        raise ValueError("missing_agent_llm_model")

    if mode == "openai":
        base_url = (
            str(env.get(ENV_BASE_URL, "") or "").strip()
            or str(env.get("OPENAI_BASE_URL", "") or "").strip()
            or DEFAULT_OPENAI_BASE_URL
        )
        api_key = (
            str(env.get(ENV_API_KEY, "") or "").strip()
            or str(env.get("OPENAI_API_KEY", "") or "").strip()
        )
        if not api_key:
            raise ValueError("missing_agent_llm_api_key")
    else:
        base_url = (
            str(env.get(ENV_BASE_URL, "") or "").strip()
            or str(env.get("OPENAI_BASE_URL", "") or "").strip()
            or DEFAULT_LOCAL_BASE_URL
        )
        api_key = (
            str(env.get(ENV_API_KEY, "") or "").strip()
            or str(env.get("OPENAI_API_KEY", "") or "").strip()
            or LOCAL_PLACEHOLDER_KEY
        )

    fallback = str(env.get(ENV_FALLBACK, "") or "").strip().lower()
    return {
        "mode": mode,
        "model": model,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "fallback": fallback,
    }


def invoke_structured_proposal(user_input: str, config: Mapping[str, str]) -> Any:
    """Call LangChain ChatOpenAI with structured output. Review-pack cite."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=config["model"],
        base_url=config["base_url"],
        api_key=config["api_key"],
        temperature=0,
    )
    structured = llm.with_structured_output(ProposalDraft)
    return structured.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
    )


class ChatCompatibleAgentLlm:
    """``local`` / ``openai`` provider: LangChain structured Proposal draft."""

    def __init__(
        self,
        name: str,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.name = name
        self._environ = environ

    def draft_proposal(
        self, user_input: str, scenario: str | None = None
    ) -> dict[str, Any]:
        del scenario  # never authority for the chat path
        text = str(user_input or "").strip()
        if not text:
            raise ValueError("missing_user_input")
        config = resolve_chat_config(self.name, self._environ)
        try:
            draft = invoke_structured_proposal(text, config)
            proposal = structured_to_proposal(draft)
        except ValueError as exc:
            if str(exc) in {
                "missing_agent_llm_model",
                "missing_agent_llm_api_key",
                "missing_user_input",
            }:
                raise
            if config["fallback"] == "stub":
                return user_input_to_proposal(text)
            raise ValueError(f"agent_llm_unavailable:{self.name}:{exc}") from exc
        except Exception as exc:  # noqa: BLE001
            if config["fallback"] == "stub":
                return user_input_to_proposal(text)
            raise ValueError(
                f"agent_llm_unavailable:{self.name}:{type(exc).__name__}"
            ) from exc
        if not proposal:
            if config["fallback"] == "stub":
                return user_input_to_proposal(text)
            raise ValueError("empty_structured_proposal")
        return proposal
