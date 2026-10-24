# Agent graph + thin ingress (optional)

One page. Run a **deterministic** LangChain / LangGraph stub that can only
`POST` a proposal to Controlled Agent Runtime. **CAR decides.** This is
**local / integration design evidence**, not production authorization and
not a Gate PASS.

## What you get

- Optional extra `.[agent]` (`httpx`, `langchain-core`, `langgraph`)
- Default `CAR_AGENT_LLM=stub` maps example Chinese/English `user_input` → structured proposal (no API key, no weight download)
- Primary path: `user_input` → proposal → Ingress (no canned `scenario` required)
- Four canned `scenario` values remain for demo / CI regression
- One HTTP hop: `POST {CAR_BASE_URL}/api/agent/propose`
- JSONL traces by default (`CAR_TRACE_JSONL` or `var/car-traces.jsonl`); optional Langfuse via current `get_client()` API when official env is complete (`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL`, or mapped `CAR_LANGFUSE_*`)
- `langfuse` is optional and is **not** part of `.[demo]`
- Core `make test` / `make demo` stay green **without** `[agent]`

## What you do not get

- No LangSmith product binding (do not set LangSmith keys for this path)
- No LangGraph `interrupt` as authoritative HITL
- No real payment / refund / industrial adapters
- No permission to execute real-world side effects
- OpenAI is **not** required; `CAR_AGENT_LLM=local` / `openai` are reserved and fail closed until an OpenAI-compatible local endpoint is implemented (no model lock-in)

## Laptop smoke

```bash
make demo                                 # terminal 1 — 127.0.0.1:8000
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00'
make agent-example SCENARIO=safe_auto     # canned demo / CI
```

Expected JSON includes `"decision": "executed"` for the seed-01-shaped proposal
or canned `safe_auto`. Other canned scenarios: `human_review` → `needs_review`;
`amount_mismatch` / `authority_attack` → `denied`.

Default origin is `http://127.0.0.1:8000`. Layout and flags:
[`examples/agent_graph/README.md`](../../examples/agent_graph/README.md).

## VPS path (existing `/hitl/` proxy)

Keep uvicorn on **loopback** `127.0.0.1:8000`. **Do not open port 8000.**

If nginx (or Caddy) already strips `/hitl/` to the uvicorn root — the same
location that serves the Human Acceptance UI — Ingress is:

```text
http://HOST/hitl/api/agent/propose
```

On the box (no public NIC):

```bash
curl -sS http://127.0.0.1:8000/api/agent/propose \
  -H 'content-type: application/json' \
  -d '{"user_input":"Please refund order_demo_001 for 100.00","proposal":{"intent":"refund","appid":"app_demo_001","term_id":"term_demo_001","original_order_no":"order_demo_001","original_transaction_date":"2026-09-01","requested_amount_minor":10000,"merchant_email":"merchant-seed01@example.invalid"},"source":"langgraph_example"}'
```

From outside, use the authenticated `/hitl/` prefix (same basic-auth /
TLS perimeter as the UI). Set the graph origin to the **strip prefix**:

```bash
CAR_BASE_URL=http://HOST/hitl make agent-example SCENARIO=safe_auto
```

`CAR_BASE_URL` + `/api/agent/propose` must equal `http://HOST/hitl/api/agent/propose`.

Alibaba Cloud / security group: allow 22 (and 80/443 only if a proxy is in
front). Do not allow 8000.

## Capability claim

Say truthfully: a stub agent stack **submits** proposals; HITL, policy, and
execution stay in CAR. JSONL (and optional Langfuse) record the path. This
does not authorize production data, real refunds, or a public launch.

See also: [2GB VPS quickstart](2gb-vps-quickstart.md),
[thin-ingress design](../superpowers/specs/2026-10-24-agent-hitl-thin-ingress-design.md).
