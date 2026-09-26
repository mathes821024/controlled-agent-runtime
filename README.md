# Controlled Agent Runtime

An evidence-first, policy-driven control plane for AI-assisted actions.

> **Project state:** Gate 0 / Inception. This repository currently defines contracts,
> policy examples, synthetic demo seeds, and engineering governance. It does **not**
> contain a production-ready action runtime or authorize real-world execution.

[中文说明](README.zh-CN.md) · [Inception index](docs/inception/00-overview.md) ·
[Policy format](policy/README.md) · [Demo seeds](demo-seeds/README.md)

## Why this exists

AI models are useful for understanding intent and proposing structured inputs, but
they should not silently become the authority for identity, business facts,
approval, idempotency, or side effects. Controlled Agent Runtime separates:

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

## Gate 0 deliverables

- Project charter, scope, trust boundaries, gate model, extraction register, and
  open questions under [`docs/inception/`](docs/inception/).
- A versioned, machine-readable policy contract and synthetic example under
  [`policy/`](policy/).
- A schema-backed synthetic refund example under [`demo-seeds/`](demo-seeds/). Seeds are `future_conformance_expectation` vectors, not proof that a Runtime already executed.
- Architecture Decision Records (ADRs), engineering governance, security policy,
  contribution guide, and public-release checklist.
- A dependency-free validation command and CI workflow for repository contracts.

## Quick validation

Requires Python 3.11+ and makes no network calls.

```bash
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
```

## Safety boundary

- Synthetic data only; reserved `.invalid` email domains are used in examples.
- No real credentials, endpoints, customer data, payment data, or production
  configuration.
- Model output is never an authoritative source for protected fields.
- Unavailable or malformed dependencies fail closed.
- A passing demo is design evidence, not production or integration evidence.

## Roadmap

The next gate may implement a minimal in-memory reference runtime after the open
questions and Gate 0 exit criteria are accepted. Database adapters, real business
connectors, deployment, and production authorization remain separate decisions.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
