"""Optional, non-authoritative proposal hook.

The default HITL demo never calls this. It exists so a later reviewed slice
can attach a *small local* model that turns natural language into candidate
proposal fields.

This module must never:

- download model weights
- emit protected / authority fields
- change policy, trusted context, or adapter results
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .models import PROTECTED_PROPOSAL_FIELDS

HOOK_ENV = "CAR_PROPOSAL_HOOK"
MODE_OFF = "off"
MODE_LOCAL_MODEL = "local_model"
ALLOWED_MODES = frozenset({MODE_OFF, MODE_LOCAL_MODEL})
OFF_ALIASES = frozenset({"", "off", "disabled", "none", "false", "0"})
LOCAL_MODEL_ALIASES = frozenset(
    {"local_model", "local-model", "localmodel", "ollama", "llm"}
)
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


class ProposalHookError(ValueError):
    """Typed fail-closed error; ``reason_code`` is stable for tests and UI."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class ProposalHookResult:
    ok: bool
    mode: str
    reason_code: str
    proposal: Optional[dict[str, Any]] = None
    download_attempted: bool = False


def resolve_proposal_hook_mode(
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    env = os.environ if environ is None else environ
    raw = str(env.get(HOOK_ENV, MODE_OFF) or MODE_OFF).strip().lower()
    if raw in OFF_ALIASES:
        return MODE_OFF
    if raw in LOCAL_MODEL_ALIASES:
        return MODE_LOCAL_MODEL
    raise ProposalHookError(f"unknown_proposal_hook_mode:{raw}")


def local_model_available(
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    """Reserved. Always false until a reviewed local-model gate exists.

    Intentionally ignores the environment: no path may trigger a download.
    """
    del environ
    return False


def sanitize_hook_proposal(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Drop or reject fields a model must never author."""
    if not isinstance(raw, Mapping):
        raise ProposalHookError("hook_proposal_not_object")
    leaked = PROTECTED_PROPOSAL_FIELDS.intersection(raw)
    if leaked:
        raise ProposalHookError(
            "proposal_contains_protected_fields:" + ",".join(sorted(leaked))
        )
    extra = set(raw) - ALLOWED_HOOK_FIELDS
    if extra:
        raise ProposalHookError(
            "proposal_contains_unknown_fields:" + ",".join(sorted(extra))
        )
    return {key: raw[key] for key in raw if key in ALLOWED_HOOK_FIELDS}


def run_proposal_hook(
    text: str,
    environ: Optional[Mapping[str, str]] = None,
) -> ProposalHookResult:
    """Turn optional free text into a proposal, or fail closed.

    Default mode is ``off``: the demo uses canned seeds and does not invent
    structured fields from language.
    """
    del text  # reserved for a future local-model slice
    try:
        mode = resolve_proposal_hook_mode(environ)
    except ProposalHookError as exc:
        return ProposalHookResult(
            ok=False,
            mode="invalid",
            reason_code=exc.reason_code,
            download_attempted=False,
        )

    if mode == MODE_OFF:
        return ProposalHookResult(
            ok=False,
            mode=mode,
            reason_code="proposal_hook_disabled",
            download_attempted=False,
        )

    if local_model_available(environ):
        return ProposalHookResult(
            ok=False,
            mode=mode,
            reason_code="local_model_path_not_implemented",
            download_attempted=False,
        )

    return ProposalHookResult(
        ok=False,
        mode=mode,
        reason_code="local_model_unavailable_no_download",
        download_attempted=False,
    )
