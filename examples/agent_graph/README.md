# Stub LangGraph example (optional)

Local / integration evidence only. Not production authorization. Not a Gate PASS.

This example drafts a **deterministic structured proposal** from `user_input`
(or an optional canned `scenario` for CI) and submits it to Controlled Agent
Runtime over HTTP. **CAR decides.** The graph has no refund / adapter / write
tools.

## What this is

- LangChain-shaped example package under `examples/agent_graph/`
- Default LLM: `CAR_AGENT_LLM=stub` (`stub_llm` maps example Chinese/English
  text → `ALLOWED_HOOK_FIELDS`; no API key, no weight download)
- Primary path: `user_input` → proposal → `POST /api/agent/propose` (no scenario)
- Optional canned `scenario` for the four demo/CI regressions
- Optional extra: `pip install -e ".[demo,agent]"` (`httpx`, `langchain-core`, `langgraph`)

## What this is not

- Not an authoritative HITL path (no LangGraph `interrupt` as approval)
- Not LangSmith
- Not a real payment rail
- `CAR_AGENT_LLM=local` / `openai` are reserved and **fail closed** until an
  OpenAI-compatible local endpoint is implemented. No model is locked.

## Install (optional)

Core `make test` / `make demo` stay green **without** this extra.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[demo,agent]"
```

## Smoke (two terminals)

Primary agent path (proposal-driven, no scenario):

```bash
make demo                  # terminal 1 — 127.0.0.1:8000
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00'
```

Canned demo / CI (unchanged four scenarios):

```bash
make agent-example SCENARIO=safe_auto
make agent-example SCENARIO=human_review      # decision=needs_review
make agent-example SCENARIO=amount_mismatch   # decision=denied
make agent-example SCENARIO=authority_attack  # decision=denied (protected field)
```

Override the origin (default `http://127.0.0.1:8000`):

```bash
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00' \
  CAR_BASE_URL=http://127.0.0.1:8000
```

On the demo VPS, nginx already proxies `/hitl/` to uvicorn root. Public ingress
is `http://HOST/hitl/api/agent/propose`. Do not open port 8000.

## Layout

| File | Role |
|---|---|
| `stub_llm.py` | user text / scenario → structured proposal. Imported by core tests (no LangGraph). |
| `llm.py` | Provider abstraction: `stub` default; `local` / `openai` reserved fail-closed. |
| `graph.py` | `understand` → `draft_proposal` → `submit_to_car` → `done`. No side-effect tools. |
| `__main__.py` | CLI: print CAR JSON |

State fields: `user_input`, `proposal`, `car_response`, `decision`, `trace_id`
(plus optional `scenario` for demo mode only).

CAR remains HITL / policy / execution authority.
