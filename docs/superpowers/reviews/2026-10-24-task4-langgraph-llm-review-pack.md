# TASK 4 LANGGRAPH + LOCAL LLM REVIEW PACK

Local / integration design evidence only. Not a Gate PASS. Not production
authorization.

**TASK 4 is not claimed PASS.** This pack is for ChatGPT re-review after
implementing a real LangChain local/openai draft path. Prior “Tasks 1–5 done”
language was too strong for the LLM claim.

**Awaiting ChatGPT review. Do not merge. Do not deploy.**

## Honest capability claims

| Mode | What it actually is | What you may say |
|---|---|---|
| `CAR_AGENT_LLM=stub` (default) | Deterministic Python mapper (`stub_llm.user_input_to_proposal`) | CI / offline fallback only. **Not** an Agent demo. |
| `CAR_AGENT_LLM=local` | LangChain `ChatOpenAI` against an OpenAI-compatible **local** base URL + `with_structured_output(ProposalDraft)` | Agent **draft** path. Still not authority. Needs a running endpoint. This repo does not pull weights. |
| `CAR_AGENT_LLM=openai` | Same client, default base `https://api.openai.com/v1`, API key required | Same draft-only claim. No model lock-in. |

CAR remains HITL / policy / execution authority. The graph cannot refund.

## How to run stub CI vs local OpenAI-compatible demo

Stub / CI (no network to a model):

```bash
make test                                 # .[demo] only; no [agent] required
make demo
CAR_AGENT_LLM=stub make agent-example \
  USER_INPUT='Please refund order_demo_001 for 100.00'
```

Local Agent draft (you already run an OpenAI-compatible server):

```bash
make demo
export CAR_AGENT_LLM=local
export CAR_AGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1   # documented default
export CAR_AGENT_LLM_MODEL=llama3.2                       # example only
make agent-example USER_INPUT='帮我退一下订单 order_demo_001，金额 100 元。'
```

`CAR_AGENT_LLM_FALLBACK=stub` is optional and **opt-in**. Default local mode
surfaces connection / JSON errors so a demo cannot silently fake an LLM.

## 1. LangGraph State

`examples/agent_graph/graph.py` `AgentState`:

| Field | Required by contract | Role |
|---|---|---|
| `user_input` | yes | Natural-language request. Tracing / draft input only. |
| `proposal` | yes | Structured untrusted overlay (`ALLOWED_HOOK_FIELDS`). |
| `car_response` | yes | Ingress JSON from CAR. |
| `decision` | yes | Copied from `car_response.decision` in `done`. |
| `trace_id` | yes | Copied from `car_response.car_trace_id` in `done`. |
| `scenario` | optional | Canned CI only. Not invented on the agent main path. |

Primary invoke (no scenario):

```python
{"user_input": "帮我退一下订单 order_demo_001，金额 100 元。", "source": "langgraph_example"}
```

## 2. Nodes / edges

```text
understand → draft_proposal → submit_to_car → done → END
```

`draft_proposal` calls `get_agent_llm().draft_proposal(user_input, scenario)`.
In local/openai mode, `scenario` is ignored as authority.

## 3. LLM provider abstraction

`examples/agent_graph/llm.py` + `examples/agent_graph/chat_llm.py`

| `CAR_AGENT_LLM` | Class | Behavior |
|---|---|---|
| `stub` | `StubAgentLlm` | Deterministic mapper. |
| `local` | `ChatCompatibleAgentLlm` | LangChain ChatOpenAI, default base `http://127.0.0.1:11434/v1`. |
| `openai` | `ChatCompatibleAgentLlm` | Same client, default base `https://api.openai.com/v1`, key required. |

Env (no model lock-in):

- `CAR_AGENT_LLM_BASE_URL` (aliases: `OPENAI_BASE_URL`)
- `CAR_AGENT_LLM_MODEL` (aliases: `OPENAI_MODEL`) — **required** for local/openai
- `CAR_AGENT_LLM_API_KEY` (aliases: `OPENAI_API_KEY`) — required for `openai`; local may use placeholder `not-needed`
- `CAR_AGENT_LLM_FALLBACK=stub` — optional; default is fail closed

## 4. Structured output schema

Pydantic `ProposalDraft` in `chat_llm.py` (same slots as `ALLOWED_HOOK_FIELDS`):

```text
intent
appid
term_id
original_order_no
original_transaction_date
requested_amount_minor
merchant_email
```

`structured_to_proposal` copies **only** those keys. `principal_id` and other
protected extras are dropped even if a model emits them.

## 5. Example user text → proposal

Primary path (no `scenario` in the Ingress body):

| user_input | Expected draft slots (stub mapper / typical local extract) |
|---|---|
| `帮我退一下订单 order_demo_001，金额 100 元。` | `order_demo_001`, `requested_amount_minor=10000` |
| `Please refund order_demo_001 for 100.00` | same |

Ingress proposal-only path still binds trusted facts from **refund-seed-01**.
Runtime / policy decide. Local LLM does not choose `human_review`.

## 6. CAR request / response shapes

`POST /api/agent/propose`

Request: `scenario` optional when a non-empty `proposal` is present;
`user_input` tracing-only.

```json
{
  "user_input": "帮我退一下订单 order_demo_001，金额 100 元。",
  "proposal": {
    "intent": "refund",
    "appid": "app_demo_001",
    "term_id": "term_demo_001",
    "original_order_no": "order_demo_001",
    "original_transaction_date": "2026-09-01",
    "requested_amount_minor": 10000,
    "merchant_email": "merchant-seed01@example.invalid"
  },
  "source": "langgraph_example"
}
```

Response `decision`: `executed | needs_review | clarify | denied`.
Proposal-only serialized `scenario` is JSON `null` (no fake name).

## 7. Tool list + proof no write tools

Graph tools: **none**.

Proof:

- `tests/test_agent_graph_stub.py::test_graph_source_only_posts_to_car_propose`
  — `graph.py` has `httpx.post` + `/api/agent/propose` and does not contain
  `mock_refund`, `/refund`, `real_adapter`, `bind_tools`, `ToolNode`, `@tool`.
- `test_chat_llm_source_uses_langchain_structured_output` — `chat_llm.py`
  has no refund/adapter calls.
- Write / refund / actuator paths stay behind CAR adapters only.

## 8. Langfuse integration method / version

Unchanged from the previous blocker (keep):

- `from langfuse import get_client`
- `get_client().start_as_current_observation(as_type="span", name=...)`
- `flush()` on end
- Official env `LANGFUSE_*`; map `CAR_LANGFUSE_*`
- Target Langfuse Python v3+ / v4; **not** a `.[demo]` dependency
- JSONL is the guaranteed sink

## 9. Tests run + results

```text
make check   # Gate 0 repository contracts: OK
make test    # .[demo] only — must stay green without a live LLM
```

Core suite does not require `.[agent]` or a running chat endpoint. Local
provider tests mock `invoke_structured_proposal` (fail-closed vs optional
stub fallback; structured schema; protected-field drop).

LangChain cite for reviewers — **this is the real call**:

```text
examples/agent_graph/chat_llm.py :: invoke_structured_proposal
  from langchain_openai import ChatOpenAI
  llm = ChatOpenAI(model=..., base_url=..., api_key=..., temperature=0)
  structured = llm.with_structured_output(ProposalDraft)
  return structured.invoke([SystemMessage(...), HumanMessage(user_input)])
```

## 10. Dependency versions (pyproject extras)

| Extra | Pins |
|---|---|
| (core) | none |
| `.[demo]` | `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `httpx>=0.27` |
| `.[agent]` | `httpx>=0.27`, `langchain-core>=0.3`, `langchain-openai>=0.2`, `langgraph>=0.2` |

`langfuse` is **not** added. `langchain-openai` is **[agent] only**.

`langchain-core` may transitively install `langsmith`. Unused. No LangSmith
product binding.

## 11. Open questions

1. Windows Mini / other OpenAI-compatible desktop endpoints: same
   `CAR_AGENT_LLM=local` + `CAR_AGENT_LLM_BASE_URL` / `CAR_AGENT_LLM_MODEL`,
   or a later named profile?
2. Should a reviewed gate pin a default local model name, or keep “model
   required, examples only”?
3. RAG remains out of scope for the refund demo. Identity / order / amount
   / state stay authoritative tools/DB — never RAG for business facts.
4. Live local-endpoint smoke was **not** run in this cloud workspace (no
   Ollama / no weight download). Code path is implemented and unit-mocked.
5. 409 vs 400 for protected proposal fields remains a review choice.

## 12. Explicit stop

**Awaiting ChatGPT review of this Task 4 LangGraph + local LLM Review Pack.**

- Task 4 is **not** claimed PASS.
- Do **not** merge this PR.
- Do **not** deploy to any host.
- Do **not** start Task 5+ feature work beyond docs already present.
- Operator VPS deploy remains a follow-up after a reviewed approval.
