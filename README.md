# Controlled Agent Runtime

An evidence-first, policy-driven control plane for AI-assisted actions.

> **Project state:** Gate 0 contracts plus a Gate 1 **reference** path on `main`:
> an in-memory `ReferenceRuntime` (Slice 1) and a local Human Acceptance UI
> (Slice 2). This is **not** a production action runtime and does **not**
> authorize real-world execution, real payments, or a public launch.

[中文说明](README.zh-CN.md) · [Inception index](docs/inception/00-overview.md) ·
[2GB VPS quickstart](docs/ops/2gb-vps-quickstart.md) ·
[Policy format](policy/README.md) · [Demo seeds](demo-seeds/README.md)

## Why this exists

AI models are useful for understanding intent and proposing structured inputs, but
they should not silently become the authority for identity, business facts,
approval, idempotency, or side effects. The first concrete pain point is
**financial refund / payment control**: a model may draft a refund proposal; it
must not invent identity, amounts, approval, or adapter success.

Controlled Agent Runtime separates:

1. **Proposal** — a model or UI proposes intent and non-authoritative fields.
2. **Authority** — trusted context, tools, and human reviewers establish facts.
3. **Policy** — deterministic rules decide whether an action is denied, paused,
   escalated, or eligible to execute.
4. **Execution** — an allowlisted adapter performs a bounded action only after all
   guards pass.
5. **Evidence** — an ordered, redacted audit trace explains what happened.

```text
untrusted proposal
       |
       v
schema validation ---> reject
       |
       v
trusted context + authoritative tool facts
       |
       v
deterministic policy ---> deny / clarify / human review
       |
       v
revalidate + authorize + idempotency
       |
       v
allowlisted adapter ---> normalized result + audit evidence
```

The private sibling `payment-controlled-agent` was an extraction source only.
This public repository is the open-source story: rewritten contracts, synthetic
data, and a small reference runtime. It does not copy private adapters or
payloads.

## What is on main today

| Layer | Status | Evidence |
|---|---|---|
| Gate 0 contracts, policy, seeds, governance | On `main` | static (`make check`) |
| Gate 1 Slice 1 `ReferenceRuntime` | On `main`, synthetic | local tests (`make test`) |
| Gate 1 Slice 2 Human Acceptance UI | On `main`, loopback FastAPI | local demo (`make demo`) |
| Real adapters, persistence, auth, production deploy | **Out of scope** | not claimed |

Owner Gate PASS / Frozen for Gate 0 and later gates remain human decisions.
Passing tests does not close a gate.

## Quick start (laptop or tiny VPS)

Requires Python 3.11+. The default demo is **offline and deterministic**. It
does not download a model and fits a ~2GB RAM CPU VPS.

```bash
make check          # contract validation, no extra deps
make test           # installs .[demo] into .venv, then tests
make demo           # http://127.0.0.1:8000  (refuses 0.0.0.0 unless opted in)
```

Open the UI and run the four scenarios. Outcomes come from `ReferenceRuntime`,
not from canned frontend success.

On a small VPS, bind loopback and use an SSH tunnel (or TLS + basic auth in
front). Do not publish port 8000 on a public NIC. One-pager:
[docs/ops/2gb-vps-quickstart.md](docs/ops/2gb-vps-quickstart.md).

An optional `CAR_PROPOSAL_HOOK=local_model` stub exists for a later small
on-box model. Default is `off`; enabling the reserved mode **fail-closes** and
never pulls weights.

## Agent ingress (optional)

A small LangChain / LangGraph **example** can submit a non-authoritative
proposal to `POST /api/agent/propose`. **CAR decides** (policy, HITL, mock
adapter). Traces are JSONL by default. Optional Langfuse uses the current
`get_client()` / `start_as_current_observation` API when
`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` are
set (or mapped from `CAR_LANGFUSE_*`). `langfuse` is not a `.[demo]`
dependency. This is local / integration evidence, **not** production.

```bash
make demo
make agent-example USER_INPUT='Please refund order_demo_001 for 100.00'
make agent-example SCENARIO=safe_auto
```

Core `make test` does not install `.[agent]`. One-pager:
[docs/ops/agent-graph-quickstart.md](docs/ops/agent-graph-quickstart.md).
On a VPS that already proxies `/hitl/` to uvicorn root, the public path is
`http://HOST/hitl/api/agent/propose`. Do not open port 8000.

## Safety boundary

- Synthetic data only; reserved `.invalid` email domains are used in examples.
- No real credentials, endpoints, customer data, payment data, or production
  configuration.
- Model output is never an authoritative source for protected fields.
- Unavailable or malformed dependencies fail closed.
- A passing demo is local design evidence, not production or integration evidence.

## Roadmap

Persistence, authenticated HITL, real adapters, and a Gate 5 deployment profile
remain separate reviewed decisions. Optional demo packaging under `deploy/demo/`
is host documentation for the loopback UI, not production authorization.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
