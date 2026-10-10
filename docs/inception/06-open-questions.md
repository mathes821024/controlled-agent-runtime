# Open questions

| ID | Question | Blocks | Safe default |
|---|---|---|---|
| OQ-01 | Is Apache-2.0 the final public license? | First public release | Do not publish until Owner confirms |
| OQ-02 | What owner/security contact should public docs name? | Vulnerability reporting UX | Use GitHub private reporting only |
| OQ-03 | Should G1 expose a library API, CLI, or both? | G1 design | Library-first, no server |
| OQ-04 | What policy expression subset is safe and understandable? | G1 evaluator | Exact-match and numeric comparisons only |
| OQ-05 | How are policy/schema versions negotiated? | Compatibility promise | Reject unsupported versions |
| OQ-06 | What evidence retention and redaction rules apply? | Persistence | In-memory synthetic evidence only |
| OQ-07 | What is the threat model for plugins/adapters? | External adapters | No dynamic plugins |
| OQ-08 | What authenticates a human reviewer? | Human-review implementation | No approval implementation |

No open question may be resolved implicitly by code. Record the decision in an ADR
or update this register before implementation.

| OQ-09 | What deterministic policy condition DSL is approved? | G1 evaluator | Keep status NOT_FROZEN; no CEL/JSONLogic/Rego/`expr` until ADR |
| OQ-10 | How is demo `refund_order_no = original_order_no + appid` made collision-safe? | Idempotency identity | Keep OPEN_QUESTION; no hash/UUID/sequence invention in Gate 0 |
| OQ-11 | How does `ALREADY_REFUNDED` (`respCode=12`) map to final normalized Runtime outcome? | Result normalization | Record contract codes now; defer final outcome mapping to ADR |

## Local-first AI + data (registered 2026-10-10; still open)

| ID | Question | Blocks | Safe default |
|---|---|---|---|
| OQ-12 | Which local LLM runtime / model family is approved for Proposal generation? | G1 Slice 3 | Do not ship a model; keep provider replaceable |
| OQ-13 | How is the local model served (process, API shape, resource limits)? | G1 Slice 3 | Defer until Slice 3 design; Runtime must not embed an SDK |
| OQ-14 | How is structured Proposal JSON enforced (schema, repair, reject)? | G1 Slice 3 | Invalid / malformed LLM output → needs_input or fail closed; never execution |
| OQ-15 | What is the first PostgreSQL schema for cases / evidence / idempotency? | G2 | No schema until G2 ADR; candidate = Docker PostgreSQL |
| OQ-16 | What evidence retention and redaction apply once persistence exists? | G2 / audit | Keep OQ-06 defaults until ADR; DB must not invent authority |
| OQ-17 | How do persisted idempotency semantics relate to in-memory G1 behavior? | G2 | In-memory semantics remain demo-only; OQ-10 still open |
| OQ-18 | Which local ASR provider is approved? | Later voice slice | Not frozen; ASR → text only |
| OQ-19 | Which local TTS provider is approved? | Later voice slice | Not frozen; TTS reads Runtime/evidence summaries only |
| OQ-20 | What threshold justifies adopting LangGraph? | Multi-step orchestration | Do not adopt until real workflow need is demonstrated |
| OQ-21 | When should Langfuse (or similar) be adopted for model tracing/eval? | Model observability | Do not adopt until eval/tracing need is demonstrated |

See also: `docs/architecture/ai-and-persistence-roadmap.md`.
