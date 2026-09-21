# ADR-0001: Separate proposal from authority

- Status: Accepted for Gate 0
- Date: 2026-09-21

## Context

Language models can extract useful structure but can also hallucinate, follow
hostile instructions, or repeat user-supplied privileged values.

## Decision

Represent model/UI output as an untrusted Proposal. TrustedContext, ToolFacts,
HumanDecision, PolicyDecision, and execution identities are separate runtime-owned
types. Protected fields supplied by a Proposal never gain authority.

## Consequences

Adapters need explicit normalized contracts. More provenance must be carried, but
security review and testing become tractable and model substitution does not
change execution authority.

