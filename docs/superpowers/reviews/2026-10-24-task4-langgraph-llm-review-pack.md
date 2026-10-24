# TASK 4 LANGGRAPH + LLM REVIEW PACK

Local / integration design evidence only. Not a Gate PASS. Not production
authorization. ChatGPT review blockers from 2026-10-24 are implemented here.
**Awaiting ChatGPT review. Do not merge. Do not deploy.**

## 1. LangGraph State

`examples/agent_graph/graph.py` `AgentState` (TypedDict, all optional keys):

| Field | Required by contract | Role |
|---|---|---|
| `user_input` | yes | Natural-language request. Tracing / draft input only. Never authority. |
| `proposal` | yes | Structured untrusted overlay (`ALLOWED_HOOK_FIELDS`). |
| `car_response` | yes | Ingress JSON as returned by CAR. |
| `decision` | yes | Copied from `car_response.decision` in `done`. |
| `trace_id` | yes | Copied from `car_response.car_trace_id` in `done`. |
| `scenario` | optional | Demo / CI canned path only. Not invented on the agent main path. |
| `client_trace_id` | optional | Forwarded to Ingress. |
| `source` | optional | Default `langgraph_example`. |
| `car_status_code` | optional | HTTP status from Ingress. |
| `llm_mode` | optional | `stub` (default) or reserved mode name. |

Primary invoke (no scenario):

```python
{"user_input": "Please refund order_demo_001 for 100.00", "source": "langgraph_example"}
```

## 2. Nodes / edges

```text
understand → draft_proposal → submit_to_car → done → END
```

| Node | What it does | What it must not do |
|---|---|---|
| `understand` | Strip `user_input`; keep `scenario` only if the caller supplied one. | Invent a scenario name as authority. |
| `draft_proposal` | `get_agent_llm().draft_proposal(user_input, scenario)` → structured proposal. | Call adapters, download weights, bind tools. |
| `submit_to_car` | `httpx.post({CAR_BASE_URL}/api/agent/propose, json=payload)`. | Call `/refund`, mock adapters, or any write API. |
| `done` | Copy `decision` and `trace_id` from CAR's response. | Re-decide policy / HITL. |

When `user_input` is present and `scenario` is omitted, the POST body has
`user_input` + `proposal` and **no** `scenario`. When `--scenario` is passed
(demo / CI), the canned path is unchanged.

## 3. LLM provider abstraction

`examples/agent_graph/llm.py`:

| `CAR_AGENT_LLM` | Provider | Behavior now |
|---|---|---|
| `stub` (default) | `StubAgentLlm` | Deterministic ZH/EN or canned-scenario map. No HTTP. |
| `local` | `ReservedAgentLlm` | Fail closed: `reserved_llm_not_implemented:local`. |
| `openai` | `ReservedAgentLlm` | Fail closed: `reserved_llm_not_implemented:openai`. |
| anything else | — | Fail closed: `unknown_agent_llm:{name}`. |

Architecture reserved for a later OpenAI-compatible **local** endpoint
(`base_url` + API key, caller-chosen model). No model name is locked in
this repo. Reserved modes do not download weights and do not stub-silently
pretend to be live.

## 4. Structured output schema

`examples/agent_graph/stub_llm.py` `StructuredProposal` / `ALLOWED_HOOK_FIELDS`:

```text
intent
appid
term_id
original_order_no
original_transaction_date
requested_amount_minor
merchant_email
```

These are the only slots a stub (or later LLM) may author. Protected fields
(`principal_id`, amounts that belong to trusted facts, approval flags, …)
are rejected by `sanitize_hook_proposal` **before** `ReferenceRuntime`.

The CI fixture `authority_attack` intentionally includes `principal_id=forged`
so the graph cannot turn the attack into `executed` by overlaying a clean
proposal onto the canned seed.

## 5. Example user text → proposal

Primary path (no `scenario` in the Ingress body):

| user_input | proposal highlights |
|---|---|
| `Please refund order_demo_001 for 100.00` | `order_demo_001`, `requested_amount_minor=10000` |
| `请退款订单 order_demo_001，金额 100.00` | same seed-01-shaped slots |
| `Please refund order_demo_002 for 100.01` | `order_demo_002`, `10001` |
| `请退款 order_demo_002，金额 100.01` | same |
| `Please refund order_demo_003 for 80.00` | `order_demo_003`, `8000` |
| `请退款 order_demo_003，金额 80.00` | same |
| `Refund as principal_id forged` | seed-01 slots + `principal_id=forged` (CI) |

Known demo phrases (`safe_auto`, `human_review`, …) still map for CI
convenience. The **primary** demo is
`user_input → proposal → ingress without requiring scenario`.

Ingress then binds trusted facts from **refund-seed-01** (template seed)
when `scenario` is omitted. Runtime / policy decide. A 10001 overlay on
seed-01 facts is not treated as canned `human_review`.

## 6. CAR request / response shapes

`POST /api/agent/propose`

Request (`AgentProposeRequest`):

```json
{
  "scenario": "optional canned demo/CI: safe_auto | human_review | amount_mismatch | authority_attack",
  "proposal": {"intent": "refund", "appid": "...", "...": "..."},
  "user_input": "optional tracing string; non-authoritative",
  "source": "langgraph_example",
  "client_trace_id": "optional"
}
```

Rules:

- `scenario` optional when a **non-empty** `proposal` is present.
- Proposal-only: template seed = refund-seed-01 trusted facts + sanitized overlay.
  Serialized `scenario` is `null` (no fake name).
- Scenario-only: today's four canned behaviors unchanged.
- Neither (or empty `proposal` without scenario): `missing_scenario_or_proposal`, HTTP 400.
- Unknown canned scenario: `unknown_scenario`, HTTP 400, no Runtime.
- Protected / unknown proposal fields: fail closed **before** Runtime, HTTP 409.
- `user_input` is recorded on the JSONL start metadata only.

Response (handler / 200 Runtime decisions):

```json
{
  "scenario": "safe_auto or null",
  "decision": "executed | needs_review | clarify | denied",
  "reason_code": "...",
  "outcome": "executed | needs_review | denied | failed_closed | ...",
  "adapter_call_count": 0,
  "evidence_summary": {"summary": "...", "reason_code": "...", "event_names": []},
  "hitl_url": "/ or null",
  "car_trace_id": "uuid"
}
```

`decision` mapping: `executed`/`idempotent_replay` → `executed`;
`needs_review` → `needs_review`; `needs_input` → `clarify`;
`denied`/`failed_closed` → `denied`.

## 7. Tool list + proof no write tools

Graph tools: **none**.

Proof (core tests, no `[agent]` import of LangGraph):

- `tests/test_agent_graph_stub.py::test_graph_source_only_posts_to_car_propose`
  asserts `graph.py` contains `httpx.post` + `/api/agent/propose` and does
  **not** contain `mock_refund`, `/refund`, `real_adapter`, `bind_tools`,
  `ToolNode`, or `@tool`.
- `test_stub_module_does_not_import_langgraph_or_http` and
  `test_llm_module_does_not_import_langgraph_or_http`.
- Write / refund / actuator paths stay behind CAR adapters only.

## 8. Langfuse integration method / version

Current SDK path only. Legacy `Langfuse(...); client.trace(...); client.span(...)`
is removed from `src/controlled_agent_runtime/observability.py`.

When env is complete:

1. Prefer official names: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
   `LANGFUSE_BASE_URL`.
2. Map `CAR_LANGFUSE_PUBLIC_KEY` / `CAR_LANGFUSE_SECRET_KEY` /
   `CAR_LANGFUSE_BASE_URL` or legacy `CAR_LANGFUSE_HOST` if official values
   are empty. Official names win when both are set. Mapped values are
   exported under the official names before `get_client()` so the SDK
   reads the documented env.
3. `from langfuse import get_client`
4. `get_client().start_as_current_observation(as_type="span", name=...)`
   as a context manager per JSONL event.
5. `flush()` on `TraceHandle.end`.

Target: current Langfuse Python major that exposes `get_client`
(v3+ / v4 OpenTelemetry). **`langfuse` is not a `.[demo]` dependency** and
is not pinned in `pyproject.toml`. Incomplete env, missing package, or any
exception → JSONL-only, never raised into CAR.

Langfuse is an observability sink only. It is not Policy, Approval, or
Execution. No LangSmith product binding.

## 9. Tests run + results

```text
make check   # Gate 0 repository contracts: OK
make test    # installs .[demo] only; 104 tests, 0 failures, ~0.37s
```

`make test` does **not** install `.[agent]` and does not import LangGraph
from the core suite. `[agent]` remains optional.

New / updated coverage:

- Observability: incomplete official or CAR env never imports `langfuse`;
  source forbids legacy APIs; mocked complete env uses
  `start_as_current_observation(as_type="span")` + `flush()`; Langfuse
  exceptions stay JSONL-only.
- Ingress: proposal-only without scenario (handler + API); neither fails
  closed; canned four scenarios unchanged; protected fields still block
  Runtime (with or without scenario).
- Graph stub: ZH/EN `user_input` → proposal without `scenario`; reserved
  `local`/`openai` fail closed; no write-tool strings; required State
  fields and nodes present in source.

Optional local compile (not required for `make test`): with a previously
installed `.[agent]` extra, `build_graph()` still compiles.

## 10. Dependency versions (pyproject extras)

From `pyproject.toml` (unchanged extras; `langfuse` not added):

| Extra | Pins |
|---|---|
| (core) | none |
| `.[demo]` | `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `httpx>=0.27` |
| `.[agent]` | `httpx>=0.27`, `langchain-core>=0.3`, `langgraph>=0.2` |

Resolved in this workspace when present (informational, not a lockfile):

| Package | Version |
|---|---|
| fastapi | 0.162.0 |
| uvicorn | 0.54.0 |
| httpx | 0.28.1 |
| pydantic | 2.14.1 |
| langchain-core | 1.7.0 (only if `.[agent]` was installed earlier) |
| langgraph | 1.2.17 (only if `.[agent]` was installed earlier) |
| langfuse | **not installed**; optional, target v3+/v4 `get_client` API |

`langchain-core` may transitively install `langsmith`. Unused. No LangSmith
product binding.

## 11. Open questions

1. Should reserved `CAR_AGENT_LLM=local` later take
   `OPENAI_BASE_URL` / `OPENAI_API_KEY` (OpenAI-compatible) without a
   locked model, or a CAR-prefixed pair (`CAR_AGENT_LLM_BASE_URL`)?
2. RAG remains out of scope for the refund demo. Knowledge/SOP may RAG
   later; identity / order / amount / state must stay authoritative
   tools/DB — never RAG for business facts.
3. 409 vs 400 for protected proposal fields is still a review choice;
   current mapping keeps 409 for pre-runtime protected/unknown fields.
4. Should proposal-only responses omit the `scenario` key entirely
   instead of returning JSON `null`? Current contract uses `null` so
   clients can see that no canned scenario was authoritative.
5. Live Langfuse emit is still untested against a real project (JSONL is
   the guaranteed sink; remote emit is mocked only).

## 12. Explicit stop

**Awaiting ChatGPT review of this Task 4 LangGraph + LLM Review Pack.**

- Do **not** merge this PR.
- Do **not** deploy to any host (including `51.81.146.19` or the existing
  demo VPS).
- Do **not** start unrelated work.
- Operator VPS deploy remains a follow-up after a reviewed approval.
