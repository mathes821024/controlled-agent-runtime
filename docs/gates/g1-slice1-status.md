# Gate 1 Slice 1 — Minimal In-Memory Reference Runtime

**Status:** Ready for ChatGPT review (not merged)  
**Frozen Gate 0 baseline:** `bd7e183290b2b33b981847f24d50b2560f31c7fa`  
**Branch:** `feat/g1-minimal-runtime`  
**Evidence date:** 2026-10-10

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

HTTP/UI/DB/Redis/real payment/LLM/LangGraph/OAuth/JWT/HITL service/deploy.

## Open questions

- OQ-08 HITL auth: still open; `needs_review` stops without fake approval
- OQ-09 Policy DSL: still open; evaluator is demo-hardcoded
- OQ-10 refund_order_no: still open; uses structured in-memory identity tuple
- OQ-11 ALREADY_REFUNDED final outcome: still open; normalize only, do not promote to success
