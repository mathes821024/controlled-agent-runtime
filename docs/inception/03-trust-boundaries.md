# Trust boundaries

## Authority matrix

| Data or decision | Allowed source | Model authority |
|---|---|---|
| User intent and ordinary slots | Model/UI proposal, then validation | Proposal only |
| Principal, tenant, application, environment | Authenticated request context | None |
| Canonical transaction or resource facts | Allowlisted authoritative Tool | None |
| Policy version and decision | Runtime policy engine | None |
| Human approval and approver identity | Authenticated review service | None |
| Idempotency identity and execution token | Runtime | None |
| Adapter result | Adapter normalization layer | None |
| Final outcome | Runtime from verified evidence | None |

## Protected fields

The example policy forbids model authority over `principal_id`, `tenant_id`,
`resource_ref`, `authorized_by`, `approval_status`, `idempotency_key`,
`execution_token`, `adapter_result`, `original_amount_minor`,
`refund_amount_minor`, and `respCode`. A future runtime may ignore forbidden
fields for audit or reject the entire proposal; it must never trust them.

## Boundary rules

- Prompt instructions cannot widen capabilities or change policy.
- Tool access is allowlisted by policy and scoped by trusted context.
- A review association token locates a case; it is not approval.
- HTTP success is not business success.
- Logs contain redacted summaries, never secrets or unnecessary raw payloads.
- Missing policy, malformed schema, unavailable authority, stale approval, failed
  revalidation, or uncertain adapter result prevents execution.

