# Runtime contract

## Conceptual inputs

- `TrustedContext`: authenticated principal, tenant, application, environment, and
  capability scope.
- `Proposal`: untrusted intent and candidate fields.
- `Policy`: versioned rules, sources, guards, outcomes, and audit requirements.
- `ToolFacts`: normalized facts returned by allowlisted authoritative tools.
- `HumanDecision`: authenticated, case-bound approval or rejection when required.

## Conceptual result

```json
{
  "outcome": "denied | needs_input | needs_review | executed | failed",
  "reason_code": "stable_machine_code",
  "policy_id": "example.refund.full.v1",
  "policy_version": "1.0.0",
  "trace_id": "trace_synthetic_001",
  "evidence": []
}
```

## Invariants

1. Proposal fields never overwrite trusted context or authoritative facts.
2. Policy evaluation is deterministic for the same normalized inputs.
3. Human approval is case-bound, actor-bound, time-bound, and insufficient without
   pre-execution revalidation.
4. Idempotency is reserved atomically before the adapter call.
5. The adapter receives the minimum required fields and no model transcript.
6. Adapter results distinguish transport, protocol, integrity/schema, and business
   outcomes.
7. Execution evidence cannot precede authorization and guard evidence.

## Error posture

Unknown policy, unknown status, unsupported schema, missing fact provenance,
timeout, malformed response, approval mismatch, state change, or idempotency
conflict returns a typed non-executing outcome.

