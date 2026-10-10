# G1 Slice 2 - Human Acceptance UI

**Status:** proposed for Owner and ChatGPT review. Not frozen. Not an implementation.
**Baseline:** `main` at `ae59cfde15bb7baaa484c07dd7d3d8ddd750a837`
**Surface:** Agent Control Room / 智能体受控执行控制台
**Prototype:** [`prototype/index.html`](prototype/index.html)

This note defines the one human surface for Gate 1 Slice 2. It is not a PRD, and it does not change policy, runtime, or scope.

## Job of the screen

A first-time reader should understand this in one view:

> The model proposes. The runtime decides. Execution requires authority, policy, and evidence.

Refund is the demo action, not the product. The product is the control path:

Proposal → Authority → Policy → Execution guard → Outcome → Evidence

The page may display a runtime result. It must not produce one.

## Design read

Professional control console for a financial-governance product. References are the information hierarchy of Linear, Stripe Dashboard, and Vercel, plus the status discipline of a security console. The palette is our own: cool paper, ink, one navy accent, and four semantic outcome colors.

Explicitly rejected: white form with three buttons, Bootstrap admin, chatbot bubbles, robot imagery, purple AI gradients, and a raw JSON page.

| Dial | Value | Why |
|---|---|---|
| Variance | 4 | The path is ordered. Asymmetry is limited to the verdict. |
| Motion | 3 | Motion only marks a scenario change and evidence order. |
| Density | 6 | Enough to compare amounts and evidence. Not a packed cockpit. |

Tokens live in the prototype `:root`. Surfaces use a 12px radius. Fields and the scenario controls use 8px. Status is never color alone.

Type: IBM Plex Sans and IBM Plex Mono, with PingFang SC and SF Pro as the Mac fallback. Icons: Phosphor Regular, decorative only. Meaning stays in text.

## Primary layout

Desktop, one screen, max width 1180px.

```text
Masthead
  Control Room
  The model proposes. The runtime decides.

Scenario switch
  Safe auto path | Human review | Amount mismatch | Authority attack

Verdict
  OUTCOME in large type
  One English sentence, then one Chinese sentence
  Adapter calls, reason, rule

Control path
  Proposal → Authority → Policy → Guard → Adapter
  Reached stations are marked and unlabeled. The station where the run stops says "Stopped here". A rejected proposal says "Rejected". Later stations say "Not reached".

Three columns
  Proposal          Judgment                 Execution
  non-authoritative authority + policy       adapter facts

Evidence timeline
  Only events this run actually recorded

Technical record
  Collapsed
```

Reading order matches the layout: conclusion, why, which rule, which authority, which evidence, then the technical record.

## Language

Chinese is the primary reading language. Every label, outcome, and explanation has an English line directly under it. Runtime identifiers such as `needs_review` and `proposal_received` stay in monospace English, with a Chinese sentence beside them.

## UX flow

1. The page opens idle. The first case is selected, but no outcome is shown.
2. The owner reads the proposal, then presses 运行这次提案 / Run this proposal.
3. Evidence rows and path stations appear one step at a time, in the real runtime order. The outcome word appears when the trace completes.
4. Switching cases clears the result and returns to idle. The page does not keep the previous answer on screen.
5. Stations the runtime never reached say 未到达 / Not reached. They are not shown as pending success.
6. After the run, selecting an evidence row marks the panel it belongs to.
7. `prefers-reduced-motion: reduce` shows the finished run immediately.

Keyboard: `1` through `4` select a case. Enter runs it when focus is on the page. The verdict region is a live region.

## Demo states

Snapshots mirror Gate 1 behavior. Amounts are integer minor units. `10000` minor = `100.00 CNY`. The threshold is authoritative amount `> 10000`.

### Safe auto path

Seed `refund-seed-01.json`.

| | |
|---|---|
| Proposal | refund, `order_demo_001`, `10000` minor |
| Authority | `principal_demo_001`, `tenant_demo_001`, `app_demo_001`, `txn_demo_001`, `10000` CNY |
| Policy | `allow_execution`, R-05, `eligible_for_guards` |
| Outcome | `executed`, `mock_business_success` |
| Adapter | mock called once, `respCode=00`, `REFUND_SUCCEEDED`. Real adapter disabled. |

Evidence, in order: `proposal_received`, `proposal_validated`, `trusted_context_bound`, `authoritative_facts_loaded`, `policy_decided`, `state_revalidated`, `idempotency_reserved`, `mock_adapter_called`, `result_normalized`, `trace_completed`.

Human line: the amounts match and sit on the 100 CNY boundary, so guards ran and the mock adapter was called once.

### Human review

Seed `refund-seed-02.json`. Proposal and authority both `10001` minor. They match. The stop is the threshold, not a mismatch.

| | |
|---|---|
| Policy | `needs_review`, R-04, `demo_amount_threshold` |
| Outcome | `needs_review` |
| Adapter calls | 0 |

Evidence stops at: `proposal_received`, `proposal_validated`, `trusted_context_bound`, `authoritative_facts_loaded`, `policy_decided`, `trace_completed`.

Not recorded: `state_revalidated`, `idempotency_reserved`, `mock_adapter_called`, `result_normalized`.

Human line: the amount is above the 100 CNY automatic-action threshold. No adapter was called. The runtime does not invent an approval.

### Amount mismatch

Seed `refund-seed-03.json`. Proposal `8000` minor. Authority `10000` minor.

| | |
|---|---|
| Policy | `deny`, R-03, `full_refund_only` |
| Outcome | `denied` |
| Adapter calls | 0 |

Evidence stops at the same six events as review. Reason is `full_refund_only`.

Not recorded: the same four execution events as review.

### Authority attack

`test_forged_principal_id_fail_closed`: seed-01 proposal plus `principal_id = forged`.

| | |
|---|---|
| Outcome | `failed_closed` |
| Reason | `proposal_contains_protected_fields:principal_id` |
| Adapter calls | 0 |

Evidence: `proposal_received`, `proposal_validated` (`fail_closed`), `trace_completed` (`fail_closed`).

Authority is not bound. Policy is not evaluated. The forged value is shown only as a rejected proposal field. It is not copied into the identity column.

## Component inventory

| Component | Role |
|---|---|
| `Masthead` | Product name and the thesis. No second destination. |
| `PrototypeNotice` | Says this page does not call the runtime. |
| `ScenarioSwitch` | Four radios. Input condition on the control. |
| `VerdictStamp` | Largest type. Outcome, why, calls, reason, rule. |
| `ControlPath` | Five stations: reached, rejected, or not reached. |
| `ProposalPanel` | Allowed fields. Marked non-authoritative. |
| `JudgmentPanel` | Authority, then policy and amount comparison. |
| `ExecutionPanel` | Call count, mock vs real, respCode, business result, idempotency. |
| `EvidenceTimeline` | Ordered recorded events, with a human gloss per event. |
| `TechnicalRecord` | Collapsed reason codes and event names. |

Empty treatment inside a panel is a sentence: what did not happen, and where the run stopped. No blank card, no skeleton that implies work is still running.

## Motion and states

- Scenario change: verdict and timeline settle in about 360ms, ease-out. Timeline rows stagger by 20ms.
- Pressed controls scale to 0.98.
- `prefers-reduced-motion: reduce` removes movement.
- Focus is a 2px ink ring. Touch targets are at least 44px.
- There is no loading state in the prototype, because nothing is fetched.

## Responsive

| Width | Behavior |
|---|---|
| `>= 1080px` | Three columns. Path is horizontal. |
| `760-1079px` | Proposal full width. Judgment and execution side by side. |
| `< 760px` | One column. Scenarios in a 2×2 grid. Path becomes a vertical list. Verdict metrics stack under the sentence. |

No horizontal page scroll. Body text stays at least 16px. The viewport uses `min-height: 100dvh`.

## Boundary for a later implementation

Not in this prototype:

- Calling `ReferenceRuntime`
- A local HTTP bridge
- Any new policy rule, identity source, or approval
- Real adapter, login, JWT/OAuth, database, Redis, LLM, LangGraph, or deployment

When implementation is separately approved, the UI stays a presentation surface. Scenario input goes in. The visible outcome, reason, adapter count, and evidence list come out of the runtime unchanged. The page must not fill unreached steps to make the timeline look complete.

## How to preview

Open `docs/ui/prototype/index.html` in a browser. No server and no install.

Switch the four scenarios and check that review, mismatch, and the authority attack stop where the tables above say they stop.
