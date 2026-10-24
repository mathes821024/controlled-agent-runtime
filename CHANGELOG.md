# Changelog

All notable changes will be documented here. The format follows Keep a Changelog
and the project intends to use Semantic Versioning after the first public API is
frozen.

## [Unreleased]

### Added

- 2GB CPU VPS Human Acceptance demo packaging: one-page quickstart, loopback
  bind guard, optional systemd unit and docker-compose (host publish stays
  `127.0.0.1`). No secrets and no assumed host password.
- Optional `CAR_PROPOSAL_HOOK` stub (`off` by default). Reserved `local_model`
  mode fail-closes and never downloads weights, so the default demo stays
  offline and deterministic on a 2GB box.

### Changed

- README / 中文说明 / changelog aligned with `main`: Gate 1 Slice 1
  `ReferenceRuntime` and Slice 2 Human Acceptance UI are present as synthetic
  local evidence. They are not a production runtime and do not close Owner gates.
- CI installs `.[demo]` so FastAPI demo tests actually run.

## Gate 1 Slice 2 (on `main`)

### Added

- Human Acceptance UI runtime integration: local FastAPI bridge
  (`POST /api/demo/run`) serves the console and returns `ReferenceRuntime`
  results. Merged as `a539ea4`.

## Gate 1 Slice 1 (on `main`)

### Added

- Minimal in-memory reference runtime, mock adapter, evidence trace, in-memory
  idempotency, and seed-01/02/03 runtime conformance tests. Merged as `ae59cfd`.

### Changed

- Review Fix 01: missing mock fixture fail-closed; layered business-success
  proof; evidence order aligned with reserve; release failed idempotency
  reservations; CNY currency fail-closed.

## Gate 0

### Changed

- Review Fix 02: add `application_id` to proposal forbidden /
  `PROTECTED_FIELDS` so trusted-context identity matches principal/tenant;
  refresh `docs/01_prd.md` baseline facts to current GitHub main (still Draft).
- Contract Freeze Review Fix 01: CNY minor-unit money contract, HITL
  threshold semantics, seed `future_conformance_expectation`, refund `respCode`
  mapping, and explicit NOT_FROZEN policy condition language.
- Expanded protected fields for refund amount / `respCode` authority.
- Added negative seeds seed-02 (HITL threshold) and seed-03 (amount mismatch).

### Added

- Gate 0 / Inception documentation.
- Policy schema and synthetic refund example.
- Demo Seed schema and Seed-01 expected evidence.
- Engineering governance and public repository skeleton.
