# Agent graph + thin ingress (optional)

One page. A LangChain / LangGraph example can only `POST` a proposal to
Controlled Agent Runtime. **CAR decides.** This is **local / integration
design evidence**, not production authorization and not a Gate PASS.

**Honest split:** `CAR_AGENT_LLM=stub` is CI / offline fallback. It is **not**
the Agent demo claim. The Agent draft path is `CAR_AGENT_LLM=local` (or
`openai`) via LangChain `ChatOpenAI` + structured output.

## What you get

- Optional extra `.[agent]` (`httpx`, `langchain-core`, `langchain-openai`, `langgraph`)
- Primary CLI: `--user-input` → structured proposal → Ingress (**no** canned `scenario`)
- Agent draft: `chat_llm.invoke_structured_proposal` → `ChatOpenAI.with_structured_output(ProposalDraft)`
- CI / offline: `CAR_AGENT_LLM=stub` deterministic mapper (no network)
- Four canned `scenario` values remain for regression only
- One graph HTTP hop: `POST {CAR_BASE_URL}/api/agent/propose`
- JSONL traces by default; optional Langfuse via current `get_client()` API
  (`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL`, or
  mapped `CAR_LANGFUSE_*`)
- `langfuse` is optional and is **not** part of `.[demo]`
- Core `make test` / `make demo` stay green **without** `[agent]`

## What you do not get

- No LangSmith product binding
- No LangGraph `interrupt` as authoritative HITL
- No real payment / refund / industrial adapters
- No weight download / Ollama pull from this repo
- No locked model name — set `CAR_AGENT_LLM_MODEL` (examples only: `llama3.2`)

## Laptop: CI stub (offline)

```bash
make demo
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00'
# default CAR_AGENT_LLM=stub — not an LLM demo
```

## Laptop: local OpenAI-compatible draft (Agent path)

Requires an endpoint you already run. Example default base:
`http://127.0.0.1:11434/v1`.

```bash
make demo
export CAR_AGENT_LLM=local
export CAR_AGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export CAR_AGENT_LLM_MODEL=llama3.2
make agent-example USER_INPUT='帮我退一下订单 order_demo_001，金额 100 元。'
```

On connection / bad JSON the graph **fail-closes** unless
`CAR_AGENT_LLM_FALLBACK=stub` is set (then do not claim an LLM demo).

Canned `SCENARIO=safe_auto` remains CI-only.

Default origin is `http://127.0.0.1:8000`. Layout:
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
  -d '{"user_input":"帮我退一下订单 order_demo_001，金额 100 元。","proposal":{"intent":"refund","appid":"app_demo_001","term_id":"term_demo_001","original_order_no":"order_demo_001","original_transaction_date":"2026-09-01","requested_amount_minor":10000,"merchant_email":"merchant-seed01@example.invalid"},"source":"langgraph_example"}'
```

From outside, use the authenticated `/hitl/` prefix. Set the graph origin to
the **strip prefix**:

```bash
CAR_BASE_URL=http://HOST/hitl make agent-example
```

`CAR_BASE_URL` + `/api/agent/propose` must equal `http://HOST/hitl/api/agent/propose`.

Alibaba Cloud / security group: allow 22 (and 80/443 only if a proxy is in
front). Do not allow 8000.

## Capability claim

Say truthfully: the example **submits** proposals; HITL, policy, and execution
stay in CAR. Stub mode is a mapper. Local mode calls an OpenAI-compatible
chat endpoint through LangChain structured output. JSONL (and optional
Langfuse) record the path. This does not authorize production data, real
refunds, or a public launch.

See also: [2GB VPS quickstart](2gb-vps-quickstart.md),
[thin-ingress design](../superpowers/specs/2026-10-24-agent-hitl-thin-ingress-design.md),
[Task 4 review pack](../superpowers/reviews/2026-10-24-task4-langgraph-llm-review-pack.md).
