# Gate 1 Slice 1 — Minimal In-Memory Reference Runtime

**Status:** Merged to `main` (`ae59cfd`, Review Fix 01 `a755d17`). Synthetic local evidence only. Not an Owner Gate PASS and not production.  
**Frozen Gate 0 baseline:** `bd7e183290b2b33b981847f24d50b2560f31c7fa`  
**Branch:** `feat/g1-minimal-runtime` (merged)  
**Evidence date:** 2026-10-10
**Review Fix 01:** missing mock dependency fail-closed; layered business
success proof; evidence order aligned with reserve; failed executions release
idempotency reservation (OQ-10 still open).

## Goal

Turn Gate 0 static contracts into a first executable reference runtime and make
seed-01 / seed-02 / seed-03 real runtime conformance tests.

## In scope

- In-memory `ReferenceRuntime`
- Deterministic refund-demo policy evaluator (no CEL/Rego/JSONLogic/eval)
- Trusted context binding
- Authoritative synthetic facts loading
- Execution guards + in-memory idempotency
- Mock refund adapter + normalization
- Ordered evidence trace
- Seed + negative invariant tests

## Out of scope (unchanged)

DB/Redis/real payment/LLM/LangGraph/OAuth/JWT/HITL service/Gate 5 deploy.
Slice 2 later added a **local** FastAPI Human Acceptance UI; it is still
synthetic, loopback-oriented, and not a production HTTP product.

## Open questions

- OQ-08 HITL auth: still open; `needs_review` stops without fake approval
- OQ-09 Policy DSL: still open; evaluator is demo-hardcoded
- OQ-10 refund_order_no: still open; uses structured in-memory identity tuple
- OQ-11 ALREADY_REFUNDED final outcome: still open; normalize only, do not promote to success
