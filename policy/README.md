# Policy contract

Policy is data reviewed by humans and evaluated deterministically by a future
Runtime. [`policy.schema.json`](policy.schema.json) defines Gate 0 structure;
[`examples/refund-demo-policy.json`](examples/refund-demo-policy.json) is synthetic.

## Required ideas

- `default_effect` must be `deny`.
- Proposal fields are allowlisted; privileged fields are explicitly forbidden.
- Trusted context and authoritative fact sources are named.
- Rules yield typed outcomes such as `deny`, `needs_input`, `needs_review`, or
  `allow_execution`.
- Execution guards require revalidation, authorization when applicable, and
  idempotency before adapter invocation.
- Audit requirements name ordered events and forbidden events.
- Real adapters remain disabled in Gate 0.

## Money contract (CNY minor units)

Gate 0 refund demo money is frozen as:

- `currency = CNY`
- representation = integer minor units only (no floats)
- `1 yuan = 100 minor units`
- `100 yuan = 10000 minor units`
- `amount_minor <= 10000` may be eligible for later automatic-path **guards**
- `amount_minor > 10000` must outcome `needs_review`

Eligibility is **not** unconditional execution. A candidate still needs
authoritative transaction lookup, full-refund consistency, protected-field
checks, authorization, idempotency, dependency availability, and execution
guards.

Proposal `requested_amount_minor` is consistency-only. Authoritative refund
amount comes from authoritative transaction facts, never from the model.

## Policy condition language

**Policy condition language is NOT FROZEN in Gate 0.**

The example `when` objects are illustrative placeholders only. Any future
evaluator must be: deterministic, side-effect free, fail closed, schema
validated, and versioned. Choosing CEL / JSONLogic / Rego / embedded expressions
is an explicit later Gate decision.

## Refund proposal fields (demo)

Minimum proposal slots for the refund demo:

- `intent` (must be `refund`)
- `appid`
- `term_id`
- `original_order_no`
- `original_transaction_date`
- optional consistency `requested_amount_minor`
- optional `merchant_email` (`.invalid` in seeds)

Full refund only. If proposal amount != authoritative `original_amount_minor`,
outcome is `deny` (`full_refund_only`).

## Authoritative transaction query

Original transaction status and amounts come only from an allowlisted
authoritative transaction query / synthetic fixture. They must not come from LLM
output, user claims of authority, prompts, or prior assistant text. Gate 0 uses
synthetic fixtures only; no real payment interfaces.

## Refund business result codes

Downstream synthetic refund results separate transport, protocol/integrity, and
business layers. Business `respCode` mapping:

- `"00"` → `REFUND_SUCCEEDED`
- `"12"` → `ALREADY_REFUNDED` (not a new refund execution success)
- other → `REFUND_FAILED`

Transport/protocol success alone never proves business success.
How `ALREADY_REFUNDED` maps to a final normalized Runtime outcome is an OPEN
QUESTION for Gate 1.

## Demo refund_order_no

Demo construction: `original_order_no + appid`.

This expresses a deterministic idempotency-key *idea* only. Delimiter ambiguity,
collision risk, and field-length limits remain an **OPEN QUESTION**. Do not
invent hash / UUID / sequence schemes in Gate 0.

## Validation scope

The JSON Schema checks shape. `scripts/validate_repository.py` checks selected
semantic invariants without claiming to be a complete policy evaluator.
