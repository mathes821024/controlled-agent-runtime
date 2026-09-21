# Governance

## Roles

- **Owner:** final Admission, Decision, and Execution Gate for project scope.
- **Maintainers:** review repository changes and releases within an admitted gate.
- **Contributors:** propose changes with evidence and respect project boundaries.

## Decision model

Material changes use an issue or ADR and record context, decision, alternatives,
consequences, and unresolved risks. Maintainer merge approval is not permission to
connect production systems, import private data, deploy, or execute real actions.
Those require explicit Owner gates with separately recorded evidence.

## Changes requiring an ADR

- trust-boundary or authority changes;
- policy semantics or protected-field changes;
- new adapters, persistence, authentication, or human-review mechanisms;
- compatibility-breaking schema changes;
- changes to default failure behavior.

## Releases

Releases require passing repository checks, a completed public-release checklist,
security review proportional to risk, and release notes that distinguish verified
facts from planned or unverified capabilities.

