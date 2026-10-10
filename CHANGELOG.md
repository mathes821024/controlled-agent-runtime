# Changelog

All notable changes will be documented here. The format follows Keep a Changelog
and the project intends to use Semantic Versioning after the first public API is
frozen.

## [Unreleased]

### Changed

- Gate 1 Slice 1 Review Fix 01: missing mock fixture fail-closed; layered
  business-success proof; evidence order aligned with reserve; release failed
  idempotency reservations; CNY currency fail-closed.

### Added

- Gate 1 Slice 1: minimal in-memory reference runtime, mock adapter, evidence
  trace, in-memory idempotency, and seed-01/02/03 runtime conformance tests
  (branch `feat/g1-minimal-runtime`; not yet merged to main).

### Changed

- Gate 0 Review Fix 02: add `application_id` to proposal forbidden /
  `PROTECTED_FIELDS` so trusted-context identity matches principal/tenant;
  refresh `docs/01_prd.md` baseline facts to current GitHub main (still Draft).

- Gate 0 Contract Freeze Review Fix 01: CNY minor-unit money contract, HITL
  threshold semantics, seed `future_conformance_expectation`, refund `respCode`
  mapping, and explicit NOT_FROZEN policy condition language.
- Expanded protected fields for refund amount / `respCode` authority.
- Added negative seeds seed-02 (HITL threshold) and seed-03 (amount mismatch).

### Added


- Gate 0 / Inception documentation.
- Policy schema and synthetic refund example.
- Demo Seed schema and Seed-01 expected evidence.
- Engineering governance and public repository skeleton.

