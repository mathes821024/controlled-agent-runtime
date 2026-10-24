# Agent + HITL Thin Ingress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a thin `POST /api/agent/propose` ingress, JSONL/Langfuse-shaped tracing, and a stub LangChain/LangGraph example that can only submit proposals to CAR — never bypass HITL/policy/adapters.

**Architecture:** Keep `ReferenceRuntime` as authority. Agent stack lives in `examples/agent_graph/` and calls Ingress over HTTP. Observability is a small internal tracer (JSONL by default; optional Langfuse env). Core `make demo` / `make test` must stay green without LangChain or Langfuse installed.

**Tech Stack:** Python 3.11+, FastAPI (existing `.[demo]`), unittest, optional `.[agent]` extras (`langchain-core`, `langgraph`, `httpx`), optional Langfuse via env (no hard CI dependency).

**Spec:** `docs/superpowers/specs/2026-10-24-agent-hitl-thin-ingress-design.md` (PR #2).

## Global Constraints

- Python `>=3.11`; no weight downloads; no Ollama pull.
- CAR remains HITL/policy/execution authority; no LangGraph interrupt as authoritative approval.
- No LangSmith; Langfuse optional; JSONL fallback always works.
- Synthetic refund vertical only; no real payment/industrial actuators.
- Do not claim Gate PASS or production authorization.
- Prefer starting from `main` (merge or rebase design PR #2 first if the plan file is not yet on `main`).
- Preserve loopback bind defaults; VPS nginx path `/hitl/` already proxies to uvicorn root (so `/api/agent/propose` is `/hitl/api/agent/propose` publicly).

## File map

| Path | Responsibility |
|---|---|
| `src/controlled_agent_runtime/observability.py` | Trace sink: JSONL + optional Langfuse-shaped emit |
| `src/controlled_agent_runtime/demo/agent_ingress.py` | Request/response models + `handle_agent_propose` |
| `src/controlled_agent_runtime/demo/app.py` | Wire `POST /api/agent/propose` |
| `tests/test_agent_ingress.py` | Ingress unit/API tests (demo extras) |
| `tests/test_observability.py` | JSONL tracer tests (no SaaS) |
| `examples/agent_graph/` | Stub LangGraph example + README |
| `pyproject.toml` | Optional `[agent]` extra |
| `Makefile` | Optional `agent-example` target |
| `docs/ops/agent-graph-quickstart.md` | One-pager how to run |
| `README.md` / `README.zh-CN.md` | Short pointer (capability-claim safe) |

---

### Task 1: Observability JSONL tracer

**Files:**
- Create: `src/controlled_agent_runtime/observability.py`
- Create: `tests/test_observability.py`

**Interfaces:**
- Produces: `start_trace(name: str, *, client_trace_id: str | None = None, metadata: dict | None = None) -> TraceHandle`
- Produces: `TraceHandle.span(name: str, **fields) -> None`, `TraceHandle.end(**fields) -> str` returning `car_trace_id`
- Produces: env `CAR_TRACE_JSONL` path (default `var/car-traces.jsonl` under cwd when writing), `CAR_LANGFUSE_PUBLIC_KEY` / `CAR_LANGFUSE_SECRET_KEY` / `CAR_LANGFUSE_HOST` optional — if unset, never import langfuse

- [ ] **Step 1: Write the failing test**

```python
# tests/test_observability.py
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.observability import start_trace


class ObservabilityTests(unittest.TestCase):
    def test_jsonl_records_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            handle = start_trace(
                "graph.run",
                client_trace_id="client-1",
                metadata={"source": "test"},
                jsonl_path=path,
            )
            handle.span("car.propose", decision="pending")
            car_id = handle.end(decision="executed")
            self.assertTrue(car_id)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 2)
            first = json.loads(lines[0])
            self.assertEqual(first["client_trace_id"], "client-1")
            self.assertEqual(first["car_trace_id"], car_id)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_observability -v`  
Expected: FAIL (module missing) after `make demo-install` if needed.

- [ ] **Step 3: Write minimal implementation**

Implement `observability.py` with in-process UUID `car_trace_id`, append-only JSONL records `{"event","name","car_trace_id","client_trace_id",...}`. If Langfuse env incomplete, skip remote. Do not raise if Langfuse import fails — stay JSONL-only.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_observability -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/controlled_agent_runtime/observability.py tests/test_observability.py
git commit -m "feat: add JSONL observability tracer for agent/CAR traces"
```

---

### Task 2: Agent propose handler (pure logic)

**Files:**
- Create: `src/controlled_agent_runtime/demo/agent_ingress.py`
- Create: `tests/test_agent_ingress.py` (logic tests without HTTP first, plus API tests)

**Interfaces:**
- Consumes: `normalize_scenario`, `build_seed_for_scenario`, `ReferenceRuntime`, `serialize_result`, `sanitize_hook_proposal`
- Produces: `AgentProposeRequest` (pydantic), `handle_agent_propose(body) -> dict` with keys `decision`, `reason_code`, `evidence_summary`, `hitl_url`, `car_trace_id`, plus passthrough runtime fields needed by tests (`outcome`, `adapter_call_count`)

Decision mapping from runtime `outcome`:
- `executed` / `idempotent_replay` → `decision="executed"`
- `needs_review` → `decision="needs_review"`, `hitl_url="/"` (UI root; public path documented as `/hitl/`)
- `needs_input` → `decision="clarify"`
- `denied` / `failed_closed` → `decision="denied"` (keep original `outcome` / `reason_code` in body for evidence)

v1 behavior:
1. Validate `source` optional string, `client_trace_id` optional, `scenario` required.
2. If `proposal` present: call `sanitize_hook_proposal`; on `ProposalHookError`, fail closed **without** calling runtime (adapter_call_count=0).
3. Else run canned seed via `build_seed_for_scenario` + `ReferenceRuntime().run_seed` (same as `/api/demo/run`).
4. Open observability trace `car.propose` / `car.decision` (and `car.adapter` span fields when adapter_call_count>0).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_agent_ingress.py (excerpt)
def test_safe_auto_via_handler(self):
    from controlled_agent_runtime.demo.agent_ingress import AgentProposeRequest, handle_agent_propose
    out = handle_agent_propose(AgentProposeRequest(scenario="safe_auto", source="test"))
    self.assertEqual(out["decision"], "executed")
    self.assertEqual(out["adapter_call_count"], 1)

def test_protected_field_in_proposal_fail_closed(self):
    from controlled_agent_runtime.demo.agent_ingress import AgentProposeRequest, handle_agent_propose
    out = handle_agent_propose(
        AgentProposeRequest(
            scenario="safe_auto",
            proposal={"intent": "refund", "principal_id": "forged"},
            source="test",
        )
    )
    self.assertEqual(out["decision"], "denied")
    self.assertEqual(out["adapter_call_count"], 0)
    self.assertIn("protected", out["reason_code"])

def test_unknown_scenario(self):
    ...
```

Also mirror four scenarios' expected outcomes from `tests/test_demo_api.py`.

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement `agent_ingress.py`**

Keep module free of FastAPI route decorators (app wires it).

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add agent propose ingress handler (sanitize + runtime)"
```

---

### Task 3: Wire FastAPI route

**Files:**
- Modify: `src/controlled_agent_runtime/demo/app.py`
- Modify: `tests/test_agent_ingress.py` (add TestClient cases) or extend `tests/test_demo_api.py`

**Interfaces:**
- Produces: `POST /api/agent/propose` → JSON from `handle_agent_propose`
- Unknown scenario → HTTP 400 with fail-closed body
- Protected proposal → HTTP 400 or 409 with `decision=denied`, `adapter_call_count=0`
- Success paths → HTTP 200

- [ ] **Step 1: Failing API test with TestClient**

```python
response = self.client.post(
    "/api/agent/propose",
    json={"scenario": "human_review", "source": "langgraph_example", "client_trace_id": "t1"},
)
self.assertEqual(response.status_code, 200)
body = response.json()
self.assertEqual(body["decision"], "needs_review")
self.assertEqual(body["adapter_call_count"], 0)
self.assertIn("car_trace_id", body)
```

- [ ] **Step 2: Run — FAIL (404)**

- [ ] **Step 3: Register route in `create_app`**

```python
from controlled_agent_runtime.demo.agent_ingress import AgentProposeRequest, handle_agent_propose

@app.post("/api/agent/propose")
def agent_propose(body: AgentProposeRequest) -> Any:
    return handle_agent_propose(body)
```

Map handler-raised / returned error shapes to status codes consistently with demo run.

- [ ] **Step 4: `make test` PASS (all existing + new)**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: expose POST /api/agent/propose on demo app"
```

---

### Task 4: Optional `[agent]` extra + stub LangGraph example

**Files:**
- Modify: `pyproject.toml` — add

```toml
agent = [
  "httpx>=0.27",
  "langchain-core>=0.3",
  "langgraph>=0.2",
]
```

- Create: `examples/agent_graph/README.md`
- Create: `examples/agent_graph/graph.py`
- Create: `examples/agent_graph/__main__.py`
- Create: `examples/agent_graph/stub_llm.py`
- Modify: `Makefile` — `agent-example` target that installs `.[demo,agent]` and runs module against `CAR_BASE_URL` default `http://127.0.0.1:8000`

**Interfaces:**
- Stub maps argv/scenario → proposal payload; **never** calls adapters.
- Node `submit_to_car` only `httpx.post(f"{base}/api/agent/propose", json=...)`.
- Default: no OpenAI. If `OPENAI_API_KEY` set, optional real draft may be added behind a flag `CAR_AGENT_LLM=openai`, but tests must use stub.
- Graph must not register tools that perform side effects.

- [ ] **Step 1: Write a lightweight test that imports stub mapping only** (no langgraph required in core CI):

`tests/test_agent_graph_stub.py` tests `stub_llm.scenario_to_payload("safe_auto")` shape — keep this file free of langgraph imports so `make test` stays green without `[agent]`.

- [ ] **Step 2: FAIL then implement stub + graph**

Minimal graph (pseudocode to implement concretely):

```python
def build_graph():
    # State: scenario, client_trace_id, car_response
    # nodes: draft_proposal -> submit_to_car -> done
    ...
```

- [ ] **Step 3: Manual smoke (document in README)**

```bash
make demo   # terminal 1
make agent-example SCENARIO=safe_auto   # terminal 2
```

Expected: JSON print with `decision=executed`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add stub LangGraph example that only proposes to CAR"
```

---

### Task 5: Docs + VPS note + capability claims

**Files:**
- Create: `docs/ops/agent-graph-quickstart.md`
- Modify: `docs/index.md` (link)
- Modify: `README.md` and `README.zh-CN.md` — short “Agent ingress (optional)” section: LangChain/LangGraph example submits proposals; CAR decides; Langfuse-shaped JSONL tracing; not production.
- Modify: `docs/ops/2gb-vps-quickstart.md` or demos nginx note: public URL `http://HOST/hitl/api/agent/propose` when using existing `/hitl/` strip proxy — **do not** open port 8000.

- [ ] **Step 1: Write docs (no code behavior change)**
- [ ] **Step 2: `make check` + `make test`**
- [ ] **Step 3: Commit**

```bash
git commit -m "docs: agent graph + thin ingress quickstart"
```

---

### Task 6: Final verification gate

- [ ] **Step 1: Run full suite**

```bash
make check && make test
```

Expected: all prior tests + new tests green; no network to Langfuse/OpenAI required.

- [ ] **Step 2: Confirm non-goals still hold** — grep example for adapter/refund HTTP besides `/api/agent/propose`; should be none.

- [ ] **Step 3: Open/update PR** describing evidence: local/integration only; lists endpoints; links spec + plan.

- [ ] **Step 4: After merge, deploy to `ubuntu@43.163.92.153`:** pull/checkout, `make demo-install`, restart `controlled-agent-demo`, curl Ingress via `http://127.0.0.1:8000/api/agent/propose` and via `http://127.0.0.1/hitl/api/agent/propose` with basic auth. (Deploy is operator follow-up; not required to merge.)

---

## Spec coverage checklist

| Spec item | Task |
|---|---|
| Thin Ingress `POST /api/agent/propose` | 2–3 |
| Sanitize protected fields | 2 |
| CAR remains authority / four scenarios | 2–3 |
| LangChain + LangGraph example stub | 4 |
| Langfuse or JSONL | 1 |
| No LangSmith / no weight download | Global + 4 |
| Docs / VPS path | 5–6 |
| Tests without SaaS | 1–3, 6 |

## Out of plan (explicit)

- OQ-08 HITL identity
- Real OpenAI as default
- LangGraph interrupt-as-HITL
- Merging classmate industrial adapters
