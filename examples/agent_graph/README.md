# Stub LangGraph example (optional)

Local / integration evidence only. Not production authorization. Not a Gate PASS.

This example drafts a **deterministic** proposal from a canned scenario and submits it to Controlled Agent Runtime over HTTP. **CAR decides.** The graph has no refund / adapter / write tools.

## What this is

- LangChain-shaped example package under `examples/agent_graph/`
- Default “LLM”: `stub_llm.scenario_to_payload` (four synthetic scenarios, no API key, no weight download)
- One HTTP call: `POST {CAR_BASE_URL}/api/agent/propose`
- Optional extra: `pip install -e ".[demo,agent]"` (`httpx`, `langchain-core`, `langgraph`)

## What this is not

- Not an authoritative HITL path (no LangGraph `interrupt` as approval)
- Not LangSmith
- Not a real payment rail
- OpenAI is **not** required. `CAR_AGENT_LLM=openai` is reserved and v1 still uses the stub (no download)

## Install (optional)

Core `make test` / `make demo` stay green **without** this extra.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[demo,agent]"
```

## Smoke (two terminals)

```bash
make demo                  # terminal 1 — 127.0.0.1:8000
make agent-example SCENARIO=safe_auto   # terminal 2
```

Expected JSON includes `"decision": "executed"` for `safe_auto`.

Other scenarios:

```bash
make agent-example SCENARIO=human_review      # decision=needs_review
make agent-example SCENARIO=amount_mismatch   # decision=denied
make agent-example SCENARIO=authority_attack  # decision=denied (protected field)
```

Override the origin (default `http://127.0.0.1:8000`):

```bash
make agent-example SCENARIO=safe_auto CAR_BASE_URL=http://127.0.0.1:8000
```

On the demo VPS, nginx already proxies `/hitl/` to uvicorn root. Public ingress is `http://HOST/hitl/api/agent/propose`. Do not open port 8000. From the box:

```bash
CAR_BASE_URL=http://127.0.0.1:8000 make agent-example SCENARIO=safe_auto
```

From outside the box (same authenticated `/hitl/` location):

```bash
CAR_BASE_URL=http://HOST/hitl make agent-example SCENARIO=safe_auto
```

## Layout

| File | Role |
|---|---|
| `stub_llm.py` | Scenario → Ingress JSON. Imported by core tests (no LangGraph). |
| `graph.py` | `draft_proposal` → `submit_to_car`. No side-effect tools. |
| `__main__.py` | CLI: print CAR JSON |

CAR remains HITL / policy / execution authority.
