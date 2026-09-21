# Engineering governance

## Change lifecycle

1. **Frame:** state problem, authority boundary, evidence class, and non-goals.
2. **Decide:** use an issue or ADR for contracts and material trade-offs.
3. **Implement:** keep the change small; write negative and invariant tests.
4. **Verify:** run focused tests, full repository checks, and inspect the diff.
5. **Review:** identify verified, skipped, and unverified claims and residual risk.
6. **Release:** apply the public-release checklist; deployment remains separate.

## Compatibility

Schemas carry explicit versions. Breaking contract changes require a new schema
version, migration guidance, and an ADR. Until version `1.0.0`, APIs may change,
but changes must still be documented.

## Testing pyramid

- schema and pure-policy unit tests;
- seed conformance and required/forbidden event assertions;
- negative tests for malformed, forged, stale, duplicate, and unavailable inputs;
- concurrency tests before persistent idempotency or review state is introduced;
- integration tests only against named, isolated test dependencies.

Skipped integration tests are reported separately and never counted as integration
proof.

## Supply chain and secrets

Minimize dependencies, pin CI actions by major version at minimum, enable automated
dependency review after publication, and never commit secrets. Examples use only
synthetic identifiers and reserved domains.

## Definition of done

A change is done only when requirements map to files/tests, checks pass freshly,
the diff is scoped, docs match behavior, and remaining risks are stated. Commit,
push, merge, release, deployment, and real execution are distinct actions.

