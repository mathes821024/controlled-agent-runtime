# Gate 0 / Inception overview

**Status:** `DRAFT_FOR_OWNER_REVIEW`  
**Gate:** `G0`  
**Data mode:** `synthetic_only`  
**Execution mode:** `disabled`

Gate 0 establishes the problem, vocabulary, boundaries, policy format, evidence
expectations, and first synthetic seed before a reusable runtime is implemented.

## Deliverable map

| Deliverable | Purpose | Exit signal |
|---|---|---|
| Charter | Define users, value, and success | Owner accepts problem and outcome |
| Scope | Bound the first runtime | Non-goals and deferred work are explicit |
| Trust boundaries | Assign authority by source | Protected fields cannot come from the model |
| Gate model | Separate admission, decision, execution, and evidence | No gate implies a later gate |
| Policy contract | Make control rules versioned and reviewable | Example validates against repository checks |
| Demo Seed | Provide one deterministic evidence scenario | Inputs and expected trace are synthetic and complete |
| Governance | Make public collaboration safe | Contribution, security, release rules exist |

## Gate 0 exit criteria

- [ ] Owner accepts the charter, scope, and non-goals.
- [ ] Owner accepts the authority matrix and protected fields.
- [ ] Policy schema versioning and default-deny behavior are accepted.
- [ ] Seed-01 inputs, expected decision, and event order are accepted.
- [ ] Open questions blocking implementation are resolved or explicitly deferred.
- [ ] Public repository name, description, license, and security contact are confirmed.
- [ ] A separate Gate 1 implementation brief is approved.

Passing local validation does not check these Owner decisions and does not close
Gate 0 automatically.

