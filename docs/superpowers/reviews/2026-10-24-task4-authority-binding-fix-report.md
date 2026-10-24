# TASK 4 AUTHORITY BINDING FIX REPORT

Local / integration design evidence only. Not a Gate PASS. Not production
authorization. **Do not merge. Do not deploy.**

Awaiting ChatGPT Gate on this Authority Binding Fix Report.

## Changed Files

| File | Change |
|---|---|
| `src/controlled_agent_runtime/demo/synthetic_transactions.py` | **new** — `SyntheticTransactionRepository` indexed from refund-seed-01/02/03 |
| `src/controlled_agent_runtime/demo/agent_ingress.py` | Proposal-only path: sanitize → lookup → bind seed; fail closed before Runtime |
| `src/controlled_agent_runtime/demo/app.py` | HTTP 400 for `authoritative_facts_unavailable` / `_mismatch` / `_ambiguous` |
| `src/controlled_agent_runtime/demo/scenarios.py` | `build_proposal_template_seed` now aliases lookup (no hardcoded seed-01) |
| `tests/test_synthetic_transactions.py` | **new** — index, 001/002 bind, unknown, mismatch, ambiguous |
| `tests/test_agent_ingress.py` | Required tests A–E plus API coverage |

Not changed: Runtime, policy, HITL, LLM (`chat_llm.py` / `llm.py`), LangGraph (`graph.py`), Langfuse (`observability.py`).

## Lookup Design

`SyntheticTransactionRepository` loads `demo-seeds/refund-seed-0{1,2,3}.json` into an in-memory index. Each record stores locator fields from the seed **proposal** plus the seed document (trusted_context, tool_fixtures, policy_ref).

Proposal-only ingress:

```text
sanitize_hook_proposal
  → extract locator (original_order_no + appid; optional term_id / date)
  → repository.lookup
  → deepcopy matched seed; overlay sanitized proposal
  → ReferenceRuntime.run_seed
```

Canned `scenario` path still uses `build_seed_for_scenario` only.

## Lookup Keys

Required: `original_order_no` + `appid`.

Optional (when the proposal supplies them, they must match): `term_id`, `original_transaction_date`.

Fail-closed reason codes (before Runtime, `adapter_call_count=0`):

| Condition | reason_code |
|---|---|
| Missing locator keys, or no row with that `original_order_no` | `authoritative_facts_unavailable` |
| Order exists but `appid` / optional term / date do not match | `authoritative_lookup_mismatch` |
| More than one row remains after filters | `authoritative_lookup_ambiguous` (never auto-pick) |

## Proposal → Authority Binding Proof

A. `order_demo_001` + `app_demo_001` binds seed-01 (`txn_demo_001`, original 10000) and follows the existing Runtime path: `decision=executed`, `adapter_call_count=1`. Evidence `authoritative_facts_loaded` summary is `resource_ref=txn_demo_001`.

## Unknown Order Behavior

B. `order_demo_999` + `requested_amount_minor=10000` (amount coincides with seed-01) → `authoritative_facts_unavailable`, `outcome=failed_closed`, `adapter_call_count=0`. `ReferenceRuntime.run_seed` is not called. Amount is not identity.

## Order-02 Threshold Proof

C. `order_demo_002` binds seed-02 facts (`txn_demo_002`, original 10001) → `needs_review` / `demo_amount_threshold`, `adapter_call_count=0`. Must not bind seed-01 and execute. Evidence shows `resource_ref=txn_demo_002`, not `txn_demo_001`.

## Cross-Resource Coincidence Test

D. `order_demo_404` + `requested_amount_minor=10000` → `authoritative_facts_unavailable`, adapter=0, Runtime not called. A coincidental amount does not select seed-01.

## Evidence Binding

Runtime still records `authoritative_facts_loaded` as `resource_ref={facts.resource_ref}` from the **looked-up** seed's `transaction_query_tool` fixture.

| Proposal order | Evidence resource_ref |
|---|---|
| `order_demo_001` | `txn_demo_001` |
| `order_demo_002` | `txn_demo_002` |

Unknown / mismatch paths fail closed before Runtime, so they have no `authoritative_facts_loaded` event (empty `event_names`).

## Tests

```text
make check   # Gate 0 repository contracts: OK
make test    # 128 tests, 0 failures (was 114)
```

Required A–E (handler):

| # | Test | Result |
|---|---|---|
| A | `test_a_proposal_only_binds_order_001` | ok — executed, adapter=1, `txn_demo_001` |
| B | `test_b_unknown_order_999_amount_10000_fail_closed` | ok — unavailable, adapter=0, no Runtime |
| C | `test_c_order_002_binds_seed_02_needs_review` | ok — needs_review, adapter=0, `txn_demo_002` |
| D | `test_d_cross_resource_coincidence_amount_is_not_identity` | ok — unavailable, adapter=0 |
| E | `test_e_locator_mismatch_order_appid_fail_closed` | ok — mismatch, adapter=0, no Runtime |

Graph no-write-tools test still green:
`test_graph_source_only_posts_to_car_propose`.

Canned four-scenario handler/API tests unchanged and green.

## Commit SHA

`cf3b780035397c6441497c80cf8eb17ca2e4e46f`

## Contract Deviations

NONE.

Lookup is synthetic and demo-seed-only. No real DB. Runtime / policy / HITL / LLM / LangGraph / Langfuse were not rewritten.

## Gate Recommendation

`TASK4_READY_FOR_REVIEW`

Tests A–E prove correct binding, unknown-order fail-closed (including amount coincidence), seed-02 threshold (not seed-01 execute), cross-resource coincidence, and locator mismatch. Awaiting ChatGPT Gate. No merge. No deploy.
