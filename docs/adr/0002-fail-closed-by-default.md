# ADR-0002: Fail closed by default

- Status: Accepted for Gate 0
- Date: 2026-09-21

## Context

Silent fallback can turn unavailable models, tools, policy, or review systems into
unexpected execution paths.

## Decision

Uncertainty or unavailable required dependencies produce a typed non-executing
outcome. No permissive fallback may be introduced without an explicit policy rule,
negative tests, and an ADR.

## Consequences

Availability may be lower, and operators need actionable reason codes. Safety
behavior is predictable and outages cannot silently broaden authority.

