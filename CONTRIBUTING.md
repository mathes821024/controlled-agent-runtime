# Contributing

Controlled Agent Runtime is currently contract-first. Small, reviewable changes
that strengthen boundaries, tests, or documentation are preferred.

## Before opening a pull request

1. Open or reference an issue for behavior or contract changes.
2. State the trust boundary and failure mode affected.
3. Add or update a synthetic seed for behavior changes.
4. Add negative tests before or with the implementation.
5. Run `make check` and `make test`.
6. Complete the pull-request safety checklist.

Do not include secrets, private interface documents, raw production payloads,
personal data, or copied proprietary implementations. By contributing, you agree
that your contribution is licensed under Apache-2.0.

## Decision authority

Maintainer review accepts a repository change. It does not authorize deployment,
production data access, external communication, or real-world side effects.

