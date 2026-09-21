# Scope and non-goals

## In scope for Gate 0

- Domain-neutral vocabulary and trust model.
- JSON Schema contracts for Policy and Demo Seed.
- One synthetic refund seed to exercise a meaningful controlled-action flow.
- Required audit-event ordering and forbidden-event assertions.
- Governance for issues, ADRs, pull requests, security, and public release.
- Dependency-free static validation.

## Explicit non-goals

- A production-ready runtime, API server, SDK, CLI, database, or UI.
- Real payment, email, document, messaging, identity, or model integrations.
- Secrets, endpoints, private payloads, customer data, or operational runbooks.
- A universal policy language or general-purpose workflow engine.
- Claims of regulatory compliance, certification, security audit, or production
  fitness.
- Migration of the private source project or compatibility with its internal API.

## Deferred gates

| Gate | Candidate outcome | Requires separate approval |
|---|---|---|
| G1 | In-memory reference evaluator and trace engine | Contract acceptance and tests |
| G2 | Persistence and concurrency controls | Storage threat model and migrations |
| G3 | Human-review reference flow | Identity and authorization contract |
| G4 | External adapter interface | Per-adapter security and failure tests |
| G5 | Deployment profile | Environment, secrets, observability, rollback |

