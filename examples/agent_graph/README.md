# LangGraph example (optional)

Local / integration evidence only. Not production authorization. Not a Gate PASS.
**Stub ≠ Agent demo claim.** `CAR_AGENT_LLM=stub` is CI / offline fallback only.

This example drafts a structured proposal from `user_input` and submits it to
Controlled Agent Runtime over HTTP **without a canned scenario**. **CAR decides.**
The graph has no refund / adapter / write tools.

## What this is

- LangChain / LangGraph example under `examples/agent_graph/`
- Primary path: `--user-input` → structured proposal → `POST /api/agent/propose`
- Agent draft path: `CAR_AGENT_LLM=local` (or `openai`) uses LangChain
  `ChatOpenAI` + `with_structured_output(ProposalDraft)` in
  `chat_llm.invoke_structured_proposal`
- CI path: `CAR_AGENT_LLM=stub` deterministic mapper (no network)
- Optional extra: `pip install -e ".[demo,agent]"` (`httpx`, `langchain-core`,
  `langchain-openai`, `langgraph`)

## What this is not

- Not an authoritative HITL path (no LangGraph `interrupt` as approval)
- Not LangSmith
- Not a real payment rail
- Stub mode is **not** a Local LLM demo
- No model name is locked. Examples (`llama3.2`, a cloud chat model) are
  documentation only — set `CAR_AGENT_LLM_MODEL`

## Install (optional)

Core `make test` / `make demo` stay green **without** this extra.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[demo,agent]"
```

## Primary demo (NL → proposal, no scenario)

Needs an OpenAI-compatible local endpoint (example: Ollama at
`http://127.0.0.1:11434/v1`). This repo does **not** pull weights.

```bash
make demo                  # terminal 1 — 127.0.0.1:8000
export CAR_AGENT_LLM=local
export CAR_AGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export CAR_AGENT_LLM_MODEL=llama3.2   # example only; use whatever the endpoint serves
make agent-example USER_INPUT='帮我退一下订单 order_demo_001，金额 100 元。'
# or
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00'
```

Connection / JSON failure **fail-closes** unless you opt in to
`CAR_AGENT_LLM_FALLBACK=stub` (then the CI mapper runs; do not call that an
LLM demo).

## CI / offline stub (not the Agent claim)

```bash
make agent-example                         # default CAR_AGENT_LLM=stub, --user-input
make agent-example SCENARIO=safe_auto      # canned regression only
```

## Layout

| File | Role |
|---|---|
| `stub_llm.py` | CI mapper. Imported by core tests (no LangGraph). |
| `llm.py` | Provider switch: stub vs ChatCompatible. |
| `chat_llm.py` | **LangChain** `ChatOpenAI.with_structured_output(ProposalDraft)`. |
| `graph.py` | `understand` → `draft_proposal` → `submit_to_car` → `done`. No write tools. |
| `__main__.py` | CLI: primary `--user-input` |

State fields: `user_input`, `proposal`, `car_response`, `decision`, `trace_id`
(plus optional `scenario` for canned CI only).

CAR remains HITL / policy / execution authority.
