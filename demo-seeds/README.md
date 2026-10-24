# Demo Seeds

A Demo Seed is a deterministic, synthetic scenario that binds a policy, inputs,
tool fixtures, expected decision, event order, and forbidden events.

## Expectation kind

Every seed sets:

```text
expectation_kind = future_conformance_expectation
```

That field is the Gate 0 contract label: the JSON describes the expected
control-plane trace. Gate 1 Slice 1 now also has a **local** `ReferenceRuntime`
that executes these seeds in-process (`make test`). That is local conformance
evidence. It is still **not** integration or production evidence, and it does
not close an Owner gate.

## Current seeds

| Seed | Scenario | Expected outcome |
|---|---|---|
| seed-01 (`refund-seed-01.json`) | Full refund at exactly 10000 minor (100.00 CNY), mock adapter `respCode=00` | `executed` (future) |
| seed-02 (`refund-seed-02.json`) | `amount_minor > 10000` | `needs_review` |
| seed-03 (`refund-seed-03.json`) | proposal amount != authoritative original | `denied` |

Money uses CNY integer minor units only (`10000` = 100 yuan, never 10000 yuan).

Validation checks schema shape and selected safety invariants. It does not prove
that a Runtime implementation exists or that a real integration is safe.
