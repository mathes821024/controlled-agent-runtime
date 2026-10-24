# Design: Agent stack + HITL thin ingress (LangChain / LangGraph / Langfuse)

**Date:** 2026-10-24  
**Repo:** `controlled-agent-runtime`  
**Status:** Draft for owner review (no implementation until approved)  
**Owner intent:** Build a reusable product skeleton that combines a strong Human-in-the-Loop (HITL) state machine with mainstream agent tech, so the same pattern can be retargeted to finance (refund/payment control) or industrial / mechatronics automation without rewriting the control plane.

## 1. Problem

Today Gate 1 proves: **model proposes → runtime decides → evidence**. The public demo is synthetic refund HITL with no LangChain / LangGraph / Langfuse. That is enough for trust-boundary teaching, but not enough as an industrial “标杆” product story: classmates and enterprise buyers already have good HITL state machines; what they lack is a clean way to **揉** real agent stacks into that loop without letting the graph become the authority for side effects.

LangSmith is intentionally out of scope (paid SaaS). First-class observability target is **self-hostable Langfuse**.

## 2. Goals

1. Keep **CAR (`ReferenceRuntime`) as the HITL / policy / execution authority**.
2. Add a **thin Proposal Ingress** so LangGraph (and any other agent) can only submit non-authoritative proposals.
3. Ship a small **LangChain + LangGraph example** that ends in `submit_to_car`, never in direct adapters.
4. Record an end-to-end trace in **Langfuse** (or local JSONL fallback when Langfuse is unset).
5. Keep the first vertical on **synthetic refund** (familiar, deterministic). Finance and industrial scenes later swap schema + policy + adapters only.

## 3. Non-goals (v1)

- LangGraph `interrupt` / resume as the *authoritative* human approval path.
- LangSmith binding.
- Real payment rails, real industrial actuators, or production Gate 5 deploy.
- Downloading general LLMs onto the ~2–4GB demo VPS by default.
- Replacing the existing `/hitl` UI in v1.

## 4. Architecture

Three layers; boundaries are hard.

```text
User / alert / ticket
        |
        v
[ Agent side ]  LangChain prompts + LangGraph graph
        |  read-only tools only (optional)
        |  structured non-authoritative proposal
        v
[ Control plane ]  CAR Proposal Ingress → ReferenceRuntime
        |  schema → trusted facts → policy → HITL UI → allowlisted adapter
        v
[ Observability ]  Langfuse (optional) + CAR evidence trace
```

### 4.1 Agent side

- **LangChain:** prompt templates + structured output (proposal schema).
- **LangGraph:** nodes roughly `understand → (optional read tools) → draft_proposal → submit_to_car → await_or_done`.
- Graph tools must not include refund / write / actuator APIs. High-risk actions exist only as CAR adapters behind policy.

### 4.2 Control plane (CAR)

- Existing runtime, policy, synthetic adapters, and Human Acceptance UI remain the source of truth for deny / clarify / needs_review / execute.
- New thin HTTP ingress only accepts proposals; it does not expose “execute now” to the graph.

### 4.3 Observability

- Prefer Langfuse self-host or cloud project key via env.
- If unset: write the same logical events to a local JSONL under a demo path so the product story still holds offline.
- Langfuse is never an approval system.

## 5. Proposal Ingress API

### 5.1 Endpoint

`POST /api/agent/propose`

Auth for v1: same perimeter as the deployed demo (e.g. nginx Basic Auth in front). Application-level HITL identity (OQ-08) stays a later gate; do not pretend Ingress auth solves reviewer identity.

### 5.2 Request (conceptual)

```json
{
  "scenario": "safe_auto | human_review | amount_mismatch | authority_attack | custom",
  "proposal": {
    "intent": "refund",
    "non_authoritative_fields": { }
  },
  "client_trace_id": "optional-langfuse-or-graph-id",
  "source": "langgraph_example"
}
```

Rules:

- Protected fields (identity, authoritative amounts, approval flags) are stripped or ignored if present (`sanitize` / existing proposal hook rules).
- Malformed bodies fail closed with a structured error; no adapter calls.

### 5.3 Response (conceptual)

```json
{
  "decision": "denied | clarify | needs_review | executed",
  "reason_code": "...",
  "evidence_summary": { },
  "hitl_url": "/hitl/... optional when needs_review",
  "car_trace_id": "..."
}
```

## 6. LangGraph example layout

Suggested path: `examples/agent_graph/` (installable optional extra, not required for `make demo` core).

- Default LLM mode: **deterministic stub** that maps the four canned scenarios (no API key, no weight download).
- Optional: `OPENAI_API_KEY` (or compatible base URL) to run a real chat model for `draft_proposal` only.
- One README in the example: how to run against local CAR and against the VPS path `/hitl/` + Ingress.

## 7. Langfuse event map

One parent trace per graph run, child spans at least:

| Span | Who | Notes |
|---|---|---|
| `graph.run` | example | input intent |
| `graph.draft_proposal` | example | raw model/stub output |
| `car.propose` | ingress | sanitized proposal |
| `car.decision` | runtime | decision + reason_code |
| `car.hitl` | runtime/UI | only if paused for human |
| `car.adapter` | runtime | mock adapter result |

Correlate with `client_trace_id` / `car_trace_id`.

## 8. Testing & evidence

- Unit: ingress sanitizes protected fields; unknown scenario fail-closed.
- Integration: stub graph → ingress → each of the four scenarios matches today’s ReferenceRuntime outcomes.
- `make check` / `make test` remain green without Langfuse or OpenAI.
- Optional smoke marked so CI does not require external SaaS.

Capability claim language: this is **local / integration design evidence** for “agent stack submits to CAR”, not production authorization.

## 9. Rollout on the demo VPS

- Keep uvicorn on `127.0.0.1:8000`.
- nginx `:80` already hosts `/hitl/`; add `/api/agent/` under the same authenticated location (or shared `/hitl` reverse proxy that already strips to backend root—ensure `/api/agent/propose` is reachable consistently with UI `/api/*`).
- Do not open new public ports unless necessary.
- Langfuse: optional compose later; v1 may be JSONL-only on the small box.

## 10. Success criteria (owner can demo)

1. Say truthfully: we use LangChain + LangGraph + Langfuse-shaped tracing.
2. Say truthfully: HITL / policy / execution stay in CAR; the graph cannot bypass them.
3. One command (or short README path) runs stub graph → visible decision in UI or API for all four scenarios.
4. Same skeleton documented as retargetable to industrial automation by swapping proposal schema, policy, and adapters.

## 11. Open follow-ups (explicitly deferred)

- OQ-08 authenticated HITL identity.
- Real adapter packs (payment private sibling; industrial classmate).
- Optional second demo path where LangGraph interrupt mirrors HITL *for teaching only*, still gated by CAR decision before side effects.
- Merging open PR #1 (2GB VPS docs) if still open when implementing.

## 12. Approval

Owner selected:

- Approach: **thin ingress** (not sidecar-only demo repo, not graph-owned HITL).
- Architecture: three-layer boundary approved.
- Ingress / graph / Langfuse mounting approved (stub LLM default).

Next after owner accepts this written spec: implementation plan via writing-plans, then Cloud Agent PR.
