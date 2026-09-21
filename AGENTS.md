# Repository instructions

This repository is at Gate 0 / Inception.

- Preserve the boundary between untrusted proposals and authoritative facts.
- Keep policy deterministic, versioned, and testable.
- Use synthetic data only; use `.invalid` domains for example email addresses.
- Never add real credentials, endpoints, customer data, payment data, or private
  source payloads.
- Fail closed when inputs, policy, approval, or dependencies are uncertain.
- Treat code/static checks, integration evidence, and production evidence as
  separate claims.
- Do not add execution adapters or deployment configuration without a separately
  reviewed gate decision.
- Run `make check` and `make test` before claiming completion.

