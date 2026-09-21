# Extraction source register

## Source boundary

The private sibling project `payment-controlled-agent` was read as an
**Extraction Source**, not used as a template repository. The source snapshot was
Git commit `c272553` on branch `feat/gate-a2-shadow`. Its untracked
`graphify-out/` directory was excluded. The source project was not modified.

This public repository contains newly written, domain-neutral contracts and
synthetic examples. It does not copy private business adapters, raw payloads,
credentials, endpoints, database configuration, operational scripts, or customer
data.

## Pattern extraction map

| Source concept | Public abstraction | Kept | Excluded |
|---|---|---|---|
| Model proposal vs trusted context | Proposal/authority separation | Protected-field rule | Business identifiers |
| Deterministic refund policy | Versioned policy document | Default deny, explicit outcomes | Private business thresholds as production truth |
| Query/refund adapters | Authoritative Tool and action Adapter | Layered result normalization | Protocol payloads and endpoints |
| HITL review | Authenticated human decision | Identity-bound approval and revalidation | Email/PDF implementation details |
| Idempotency and requery | Pre-execution guards | Required guard sequence | Database implementation |
| Audit events | Ordered evidence contract | Typed, redacted events | Raw private responses |
| Seed-01 | Synthetic Demo Seed | Full-refund example shape | Compatibility promise with source code |

## Provenance classes

- `extracted_pattern`: generalized from observed design and code structure.
- `new_public_contract`: authored for this repository.
- `synthetic_example`: invented data under reserved domains.
- `open_question`: not established and not silently treated as truth.

## Reuse rule

Future contributions may re-express general patterns after independent review.
They must not copy source code or private artifacts unless provenance, license,
and explicit publication authority are established first.

