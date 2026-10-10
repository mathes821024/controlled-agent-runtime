"""Minimal in-memory reference runtime (Gate 1 Slice 1)."""

from __future__ import annotations

from typing import Any, Mapping, Optional
from uuid import uuid4

from .adapters.mock_refund import MockAdapterRequest, MockRefundAdapter
from .evidence import EvidenceTrace
from .idempotency import IdempotencyIdentity, InMemoryIdempotencyStore
from .models import (
    AuthoritativeFacts,
    DecisionOutcome,
    Proposal,
    RuntimeOutcome,
    RuntimeResult,
    TrustedContext,
)
from .policy import evaluate_refund_demo_policy


class ReferenceRuntime:
    """Deterministic control-plane reference: Proposal ≠ Authority."""

    def __init__(
        self,
        *,
        idempotency_store: Optional[InMemoryIdempotencyStore] = None,
    ) -> None:
        self.idempotency_store = idempotency_store or InMemoryIdempotencyStore()

    def run_seed(self, seed: Mapping[str, Any]) -> RuntimeResult:
        return self.run(
            proposal_raw=seed.get("proposal") or {},
            trusted_context_raw=seed.get("trusted_context") or {},
            transaction_fixture=(seed.get("tool_fixtures") or {}).get(
                "transaction_query_tool"
            )
            or {},
            mock_adapter_fixture=(seed.get("tool_fixtures") or {}).get(
                "mock_refund_adapter"
            ),
        )

    def run(
        self,
        *,
        proposal_raw: Mapping[str, Any],
        trusted_context_raw: Mapping[str, Any],
        transaction_fixture: Mapping[str, Any],
        mock_adapter_fixture: Optional[Mapping[str, Any]] = None,
    ) -> RuntimeResult:
        trace = EvidenceTrace()
        adapter = MockRefundAdapter(mock_adapter_fixture)
        decision = None

        try:
            trace.record("proposal_received", summary="proposal accepted for validation")

            try:
                proposal = Proposal.from_mapping(proposal_raw)
            except ValueError as exc:
                trace.record(
                    "proposal_validated",
                    summary="fail_closed",
                    reason_code=str(exc),
                )
                trace.record("trace_completed", reason_code="fail_closed")
                return RuntimeResult(
                    outcome=RuntimeOutcome.FAILED_CLOSED,
                    reason_code=str(exc),
                    decision=None,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                    summary="proposal rejected",
                )

            trace.record("proposal_validated", summary="proposal fields allowed")

            try:
                trusted = TrustedContext.from_mapping(trusted_context_raw)
            except ValueError as exc:
                trace.record(
                    "trusted_context_bound",
                    summary="fail_closed",
                    reason_code=str(exc),
                )
                trace.record("trace_completed", reason_code="fail_closed")
                return RuntimeResult(
                    outcome=RuntimeOutcome.FAILED_CLOSED,
                    reason_code=str(exc),
                    decision=None,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                    summary="trusted context missing",
                )

            trace.record(
                "trusted_context_bound",
                summary="authenticated context bound",
            )

            try:
                facts = AuthoritativeFacts.from_mapping(transaction_fixture)
            except ValueError as exc:
                trace.record(
                    "authoritative_facts_loaded",
                    summary="fail_closed",
                    reason_code=str(exc),
                )
                trace.record("trace_completed", reason_code="fail_closed")
                return RuntimeResult(
                    outcome=RuntimeOutcome.FAILED_CLOSED,
                    reason_code=str(exc),
                    decision=None,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                    summary="authoritative facts unavailable",
                )

            trace.record(
                "authoritative_facts_loaded",
                summary=f"resource_ref={facts.resource_ref}",
            )

            decision = evaluate_refund_demo_policy(proposal, facts)
            trace.record(
                "policy_decided",
                summary=decision.outcome.value,
                reason_code=decision.reason_code,
            )

            if decision.outcome == DecisionOutcome.DENY:
                trace.record("trace_completed", reason_code=decision.reason_code)
                return RuntimeResult(
                    outcome=RuntimeOutcome.DENIED,
                    reason_code=decision.reason_code,
                    decision=decision,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                )

            if decision.outcome == DecisionOutcome.NEEDS_INPUT:
                trace.record("trace_completed", reason_code=decision.reason_code)
                return RuntimeResult(
                    outcome=RuntimeOutcome.NEEDS_INPUT,
                    reason_code=decision.reason_code,
                    decision=decision,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                )

            if decision.outcome == DecisionOutcome.NEEDS_REVIEW:
                # HITL required; no fake approval (OQ-08 open).
                trace.record("trace_completed", reason_code=decision.reason_code)
                return RuntimeResult(
                    outcome=RuntimeOutcome.NEEDS_REVIEW,
                    reason_code=decision.reason_code,
                    decision=decision,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                )

            # allow_execution → guards
            refund_amount = facts.original_amount_minor
            identity = IdempotencyIdentity(
                tenant_id=trusted.tenant_id,
                application_id=trusted.application_id,
                principal_id=trusted.principal_id,
                resource_ref=facts.resource_ref,
                original_order_no=proposal.original_order_no,
                appid=proposal.appid,
                refund_amount_minor=refund_amount,
            )

            existing = self.idempotency_store.get(identity)
            if existing is not None and existing.outcome in {
                RuntimeOutcome.EXECUTED,
                RuntimeOutcome.IDEMPOTENT_REPLAY,
            }:
                # Fresh trace for this call: prove no second adapter invocation.
                replay_trace = EvidenceTrace()
                replay_trace.record("proposal_received", summary="duplicate identity")
                replay_trace.record("proposal_validated")
                replay_trace.record("trusted_context_bound")
                replay_trace.record("authoritative_facts_loaded")
                replay_trace.record(
                    "policy_decided",
                    summary=decision.outcome.value,
                    reason_code=decision.reason_code,
                )
                replay_trace.record(
                    "idempotency_hit",
                    summary="prior execution reused; adapter not called",
                    reason_code="idempotent_replay",
                )
                replay_trace.record("trace_completed", reason_code="idempotent_replay")
                return RuntimeResult(
                    outcome=RuntimeOutcome.IDEMPOTENT_REPLAY,
                    reason_code="idempotent_replay",
                    decision=decision,
                    adapter_call_count=0,
                    evidence=replay_trace.events,
                    normalized_business_result=existing.normalized_business_result,
                    resp_code=existing.resp_code,
                    execution_token=existing.execution_token,
                    idempotency_key=existing.idempotency_key,
                    summary="duplicate action identity; adapter not called",
                )

            # Revalidate before side effects.
            if proposal.requested_amount_minor != facts.original_amount_minor:
                trace.record(
                    "state_revalidated",
                    summary="fail_closed",
                    reason_code="full_refund_only",
                )
                trace.record("trace_completed", reason_code="full_refund_only")
                return RuntimeResult(
                    outcome=RuntimeOutcome.DENIED,
                    reason_code="full_refund_only",
                    decision=decision,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                )
            if facts.original_amount_minor > 10000:
                trace.record(
                    "state_revalidated",
                    summary="fail_closed",
                    reason_code="demo_amount_threshold",
                )
                trace.record("trace_completed", reason_code="demo_amount_threshold")
                return RuntimeResult(
                    outcome=RuntimeOutcome.NEEDS_REVIEW,
                    reason_code="demo_amount_threshold",
                    decision=decision,
                    adapter_call_count=adapter.call_count,
                    evidence=trace.events,
                )

            execution_token = f"exec_{uuid4().hex}"
            idempotency_key = f"idem_{uuid4().hex}"
            placeholder = RuntimeResult(
                outcome=RuntimeOutcome.FAILED_CLOSED,
                reason_code="in_flight",
                decision=decision,
                adapter_call_count=0,
                evidence=[],
                execution_token=execution_token,
                idempotency_key=idempotency_key,
            )
            reserved = self.idempotency_store.reserve(identity, placeholder)
            if not reserved:
                existing = self.idempotency_store.get(identity)
                assert existing is not None
                trace.record(
                    "idempotency_hit",
                    summary="reservation raced; adapter not called",
                    reason_code="idempotent_replay",
                )
                trace.record("trace_completed", reason_code="idempotent_replay")
                return RuntimeResult(
                    outcome=RuntimeOutcome.IDEMPOTENT_REPLAY,
                    reason_code="idempotent_replay",
                    decision=decision,
                    adapter_call_count=0,
                    evidence=trace.events,
                    normalized_business_result=existing.normalized_business_result,
                    resp_code=existing.resp_code,
                    execution_token=existing.execution_token,
                    idempotency_key=existing.idempotency_key,
                    summary="duplicate action identity; adapter not called",
                )

            trace.record("state_revalidated", summary="guards still hold")
            trace.record(
                "idempotency_reserved",
                summary="in_memory_reservation",
            )

            response = adapter.execute(
                MockAdapterRequest(
                    resource_ref=facts.resource_ref,
                    refund_amount_minor=refund_amount,
                    currency=facts.currency,
                    original_order_no=proposal.original_order_no,
                    appid=proposal.appid,
                    execution_token=execution_token,
                )
            )
            trace.record(
                "mock_adapter_called",
                summary=f"respCode={response.respCode}",
            )

            # Transport/protocol success ≠ business success.
            business_ok = (
                response.transport_status == "success"
                and response.protocol_status == "success"
                and response.respCode == "00"
                and response.normalized_business_result == "REFUND_SUCCEEDED"
            )
            if response.respCode == "12":
                # OQ-11: do not invent final runtime outcome beyond normalization.
                normalized = "ALREADY_REFUNDED"
                outcome = RuntimeOutcome.FAILED_CLOSED
                reason = "already_refunded_outcome_unmapped"
                summary = "respCode=12 normalized; final outcome mapping open (OQ-11)"
            elif business_ok:
                normalized = "REFUND_SUCCEEDED"
                outcome = RuntimeOutcome.EXECUTED
                reason = "mock_business_success"
                summary = "mock refund succeeded"
            else:
                normalized = response.normalized_business_result or "REFUND_FAILED"
                outcome = RuntimeOutcome.FAILED_CLOSED
                reason = "mock_business_failed"
                summary = "adapter did not prove refund success"

            trace.record(
                "result_normalized",
                summary=normalized,
                reason_code=reason,
            )
            trace.record("trace_completed", reason_code=reason)

            result = RuntimeResult(
                outcome=outcome,
                reason_code=reason,
                decision=decision,
                adapter_call_count=adapter.call_count,
                evidence=trace.events,
                normalized_business_result=normalized,
                resp_code=response.respCode,
                execution_token=execution_token,
                idempotency_key=idempotency_key,
                summary=summary,
            )
            if outcome == RuntimeOutcome.EXECUTED:
                self.idempotency_store.complete(identity, result)
            return result

        except Exception as exc:  # fail closed
            trace.record("trace_completed", reason_code="fail_closed")
            return RuntimeResult(
                outcome=RuntimeOutcome.FAILED_CLOSED,
                reason_code=f"unexpected:{type(exc).__name__}",
                decision=decision,
                adapter_call_count=adapter.call_count,
                evidence=trace.events,
                summary=str(exc),
            )
