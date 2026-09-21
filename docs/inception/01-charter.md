# Project charter

## Problem

AI-assisted workflows often blur language understanding, business authority, and
side effects. A plausible model response can then be mistaken for a verified fact
or an execution decision. Teams need a small, reusable control plane that makes
authority, policy, human review, idempotency, and evidence explicit.

## Mission

Provide an open, domain-neutral reference runtime for converting untrusted agent
proposals into bounded, policy-governed actions with explainable evidence.

## Primary users

- application engineers adding AI assistance to action workflows;
- security and risk reviewers defining non-bypassable controls;
- domain owners who must approve policy and execution boundaries;
- auditors and operators who need traceable outcomes.

## Gate 0 success

Success is a coherent, public-safe contract set that another engineer can review
without access to the private extraction source. It must make clear what is
authoritative, what is proposed, when execution is forbidden, and what evidence a
future runtime must emit.

## Principles

1. Proposal is not authority.
2. Policy is deterministic and versioned.
3. Uncertainty fails closed.
4. Human review is an authenticated decision, not a message or token.
5. Revalidation and idempotency happen immediately before execution.
6. Adapter outcomes are normalized across transport, protocol, schema, and
   business layers.
7. Evidence claims remain proportional to what was actually tested.

