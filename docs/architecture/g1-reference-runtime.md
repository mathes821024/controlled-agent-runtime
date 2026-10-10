# G1 Reference Runtime Architecture Note

## Pipeline

```text
proposal_received
  → proposal_validated
  → trusted_context_bound
  → authoritative_facts_loaded
  → policy_decided
  → [deny | needs_input | needs_review] STOP (no adapter)
  → allow_execution
  → state_revalidated
  → idempotency_reserved
  → mock_adapter_called
  → result_normalized
  → trace_completed
```

## Authority split

| Concern | Source |
|---|---|
| Proposal slots (`intent`, `appid`, …) | Proposal |
| `principal_id` / `tenant_id` / `application_id` | Trusted context only |
| `resource_ref` / `original_amount_minor` | Transaction fixture / tool |
| Policy decision | Deterministic evaluator |
| Adapter result / `respCode` | Mock adapter normalizer |

`appid` ≠ `application_id`.

## Modules

- `models.py` — domain types
- `policy.py` — refund demo evaluator
- `runtime.py` — orchestration
- `evidence.py` — ordered events
- `idempotency.py` — in-memory reservation
- `adapters/mock_refund.py` — synthetic adapter
