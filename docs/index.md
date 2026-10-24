# Documentation index

## Inception

- [Overview](inception/00-overview.md)
- [Charter](inception/01-charter.md)
- [Scope and non-goals](inception/02-scope-and-non-goals.md)
- [Trust boundaries](inception/03-trust-boundaries.md)
- [Gate and evidence model](inception/04-gate-and-evidence-model.md)
- [Extraction source register](inception/05-extraction-source.md)
- [Open questions](inception/06-open-questions.md)

## Gate 1 (synthetic reference on `main`)

- [Slice 1 — reference runtime](gates/g1-slice1-status.md)
- [Slice 2 — Human Acceptance UI](gates/g1-slice2-human-ui.md)
- [Reference runtime architecture](architecture/g1-reference-runtime.md)
- [Human Acceptance UI note](ui/g1-human-acceptance-ui.md)

## Operations (demo only)

- [2GB VPS quickstart](ops/2gb-vps-quickstart.md) — loopback HITL demo, no LLM
- [Agent graph + thin ingress](ops/agent-graph-quickstart.md) — optional stub proposes; CAR decides; do not open port 8000

## Architecture and governance

- [Runtime contract](architecture/runtime-contract.md)
- [Design: Agent stack + HITL thin ingress](superpowers/specs/2026-10-24-agent-hitl-thin-ingress-design.md)
- [Plan: Agent stack + HITL thin ingress](superpowers/plans/2026-10-24-agent-hitl-thin-ingress.md)
- [TASK 4 LangGraph + local LLM review pack](superpowers/reviews/2026-10-24-task4-langgraph-llm-review-pack.md) — Task 4 not yet PASS; awaiting ChatGPT review; no merge; no deploy
- [TASK 4 authority binding fix report](superpowers/reviews/2026-10-24-task4-authority-binding-fix-report.md) — awaiting ChatGPT Gate; no merge; no deploy
- [ADR-0001: authority separation](adr/0001-separate-proposal-from-authority.md)
- [ADR-0002: fail closed](adr/0002-fail-closed-by-default.md)
- [Engineering governance](governance/engineering-governance.md)
- [AI workstation](governance/ai-workstation.md)
- [Public release checklist](governance/public-release-checklist.md)
