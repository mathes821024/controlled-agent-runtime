# Gate and evidence model

## Human project gates

| Gate | Question | Output |
|---|---|---|
| Admission Gate | Is this problem and data allowed into the project? | Scope and data boundary |
| Decision Gate | Is the proposed design or policy accepted? | Recorded decision/ADR |
| Execution Gate | Is this exact side effect authorized now? | Scoped authorization |
| Evidence Gate | What can current evidence actually prove? | Bounded claim and residual risk |

Acceptance at one gate never implies acceptance at a later gate. In particular,
merging code is not deployment or execution authorization.

## Runtime gates

```text
G0 input admitted
G1 proposal schema valid
G2 trusted context bound
G3 authoritative facts loaded
G4 deterministic policy decided
G5 authenticated human decision bound (when required)
G6 state revalidated
G7 idempotency reserved
G8 allowlisted adapter invoked
G9 normalized result and evidence finalized
```

Every gate emits an ordered event. A failed gate emits a typed reason and no later
execution event. The Demo Seed expresses both required order and forbidden events.

## Evidence classes

- `static`: documents, schemas, code inspection, linting.
- `local_runtime`: deterministic execution against synthetic local fixtures.
- `integration`: behavior against a named external test dependency.
- `production`: observed deployed version and production-safe evidence.

Evidence from one class must not be reported as a stronger class.

