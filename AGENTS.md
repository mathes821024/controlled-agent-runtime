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

## AI workstation

Collaboration uses one Mac workstation: Think → See → Decide → Freeze → Build →
Verify. See [`docs/governance/ai-workstation.md`](docs/governance/ai-workstation.md).

- ChatGPT controls and reviews. Mac Cursor holds one design role at a time.
  Mac Grok Bot is the primary engineer. GitHub is the only remote source of truth.
- Another Cursor account is capacity backup for this same workspace, not another
  workstation.
- Only one agent writes at a time. `@role` does not grant commit, push, or deploy.

