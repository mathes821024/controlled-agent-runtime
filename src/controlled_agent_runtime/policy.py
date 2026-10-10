"""Deterministic refund demo policy evaluator (Gate 1).

Does not introduce CEL/Rego/JSONLogic/eval. Logic is hardcoded to the Gate 0
refund demo rules. Policy DSL remains NOT_FROZEN (OQ-09).
"""

from __future__ import annotations

from .models import (
    HITL_THRESHOLD_EXCLUSIVE_MINOR,
    REQUIRED_PROPOSAL_FIELDS,
    AuthoritativeFacts,
    DecisionOutcome,
    PolicyDecision,
    Proposal,
)


def evaluate_refund_demo_policy(
    proposal: Proposal,
    facts: AuthoritativeFacts,
) -> PolicyDecision:
    if proposal.intent != "refund":
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code="unsupported_intent",
            rule_id="R-01",
        )

    missing = [
        name
        for name in REQUIRED_PROPOSAL_FIELDS
        if not str(getattr(proposal, name, "") or "").strip()
    ]
    if missing:
        return PolicyDecision(
            outcome=DecisionOutcome.NEEDS_INPUT,
            reason_code="required_field_missing",
            rule_id="R-02",
        )

    if proposal.requested_amount_minor is None:
        return PolicyDecision(
            outcome=DecisionOutcome.NEEDS_INPUT,
            reason_code="required_field_missing",
            rule_id="R-02",
        )

    # Consistency only: proposal amount is never authoritative execution amount.
    if proposal.requested_amount_minor != facts.original_amount_minor:
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code="full_refund_only",
            rule_id="R-03",
        )

    # HITL uses authoritative amount (equals proposal after R-03).
    if facts.original_amount_minor > HITL_THRESHOLD_EXCLUSIVE_MINOR:
        return PolicyDecision(
            outcome=DecisionOutcome.NEEDS_REVIEW,
            reason_code="demo_amount_threshold",
            rule_id="R-04",
        )

    return PolicyDecision(
        outcome=DecisionOutcome.ALLOW_EXECUTION,
        reason_code="eligible_for_guards",
        rule_id="R-05",
    )
