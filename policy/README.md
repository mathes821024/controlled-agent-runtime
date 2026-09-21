# Policy contract

Policy is data reviewed by humans and evaluated deterministically by the future
Runtime. [`policy.schema.json`](policy.schema.json) defines Gate 0 structure;
[`examples/refund-demo-policy.json`](examples/refund-demo-policy.json) is synthetic.

## Required ideas

- `default_effect` must be `deny`.
- Proposal fields are allowlisted; privileged fields are explicitly forbidden.
- Trusted context and authoritative fact sources are named.
- Rules yield typed outcomes such as `deny`, `needs_input`, `needs_review`, or
  `allow_execution`.
- Execution guards require revalidation, authorization when applicable, and
  idempotency before adapter invocation.
- Audit requirements name ordered events and forbidden events.
- Real adapters remain disabled in Gate 0.

The JSON Schema checks shape. `scripts/validate_repository.py` checks selected
semantic invariants without claiming to be a complete policy evaluator.

