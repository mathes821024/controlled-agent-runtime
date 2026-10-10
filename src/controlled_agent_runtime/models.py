"""Gate 1 domain types for the minimal in-memory reference runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


PROTECTED_PROPOSAL_FIELDS = frozenset(
    {
        "principal_id",
        "tenant_id",
        "application_id",
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
)

REQUIRED_PROPOSAL_FIELDS = (
    "intent",
    "appid",
    "term_id",
    "original_order_no",
    "original_transaction_date",
)

HITL_THRESHOLD_EXCLUSIVE_MINOR = 10000


class DecisionOutcome(str, Enum):
    DENY = "deny"
    NEEDS_INPUT = "needs_input"
    NEEDS_REVIEW = "needs_review"
    ALLOW_EXECUTION = "allow_execution"


class RuntimeOutcome(str, Enum):
    DENIED = "denied"
    NEEDS_INPUT = "needs_input"
    NEEDS_REVIEW = "needs_review"
    EXECUTED = "executed"
    FAILED_CLOSED = "failed_closed"
    IDEMPOTENT_REPLAY = "idempotent_replay"


@dataclass(frozen=True)
class Proposal:
    """Non-authoritative proposal fields only."""

    intent: str
    appid: str
    term_id: str
    original_order_no: str
    original_transaction_date: str
    requested_amount_minor: Optional[int] = None
    merchant_email: Optional[str] = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Proposal":
        unknown_protected = PROTECTED_PROPOSAL_FIELDS.intersection(raw)
        if unknown_protected:
            raise ValueError(
                "proposal_contains_protected_fields:"
                + ",".join(sorted(unknown_protected))
            )
        allowed = {
            "intent",
            "appid",
            "term_id",
            "original_order_no",
            "original_transaction_date",
            "requested_amount_minor",
            "merchant_email",
        }
        extra = set(raw) - allowed
        if extra:
            raise ValueError("proposal_contains_unknown_fields:" + ",".join(sorted(extra)))
        amount = raw.get("requested_amount_minor")
        if amount is not None and type(amount) is not int:
            raise ValueError("requested_amount_minor_must_be_int")
        if amount is not None and isinstance(amount, bool):
            raise ValueError("requested_amount_minor_must_be_int")
        return cls(
            intent=str(raw.get("intent", "")),
            appid=str(raw.get("appid", "")),
            term_id=str(raw.get("term_id", "")),
            original_order_no=str(raw.get("original_order_no", "")),
            original_transaction_date=str(raw.get("original_transaction_date", "")),
            requested_amount_minor=amount,
            merchant_email=None if raw.get("merchant_email") is None else str(raw["merchant_email"]),
        )


@dataclass(frozen=True)
class TrustedContext:
    principal_id: str
    tenant_id: str
    application_id: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "TrustedContext":
        required = ("principal_id", "tenant_id", "application_id")
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise ValueError("trusted_context_missing:" + ",".join(missing))
        return cls(
            principal_id=str(raw["principal_id"]),
            tenant_id=str(raw["tenant_id"]),
            application_id=str(raw["application_id"]),
        )


@dataclass(frozen=True)
class AuthoritativeFacts:
    found: bool
    resource_ref: str
    original_amount_minor: int
    transaction_status: str
    currency: str = "CNY"

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "AuthoritativeFacts":
        if not raw or not raw.get("found"):
            raise ValueError("authoritative_facts_unavailable")
        amount = raw.get("original_amount_minor")
        if type(amount) is not int or isinstance(amount, bool):
            raise ValueError("authoritative_original_amount_invalid")
        resource_ref = raw.get("resource_ref")
        if not resource_ref:
            raise ValueError("authoritative_resource_ref_missing")
        return cls(
            found=True,
            resource_ref=str(resource_ref),
            original_amount_minor=amount,
            transaction_status=str(raw.get("transaction_status", "")),
            currency=str(raw.get("currency", "CNY")),
        )


@dataclass(frozen=True)
class PolicyDecision:
    outcome: DecisionOutcome
    reason_code: str
    rule_id: str


@dataclass(frozen=True)
class EvidenceEvent:
    name: str
    sequence: int
    summary: str = ""
    reason_code: str = ""


@dataclass
class RuntimeResult:
    outcome: RuntimeOutcome
    reason_code: str
    decision: Optional[PolicyDecision]
    adapter_call_count: int
    evidence: list[EvidenceEvent] = field(default_factory=list)
    normalized_business_result: Optional[str] = None
    resp_code: Optional[str] = None
    execution_token: Optional[str] = None
    idempotency_key: Optional[str] = None
    summary: str = ""

    def event_names(self) -> list[str]:
        return [e.name for e in self.evidence]
