# Local-first AI + Local Docker Data — Roadmap

**Status:** Planning direction (Owner confirmed)  
**Baseline `main`:** `a539ea456cd7a4de1a32952036d0ac80d0b0bbfd`  
**Evidence date:** 2026-10-10  
**Not an implementation authorization.** No model, DB, docker-compose, or framework dependency is introduced by this document.

## Core principle

> AI can misunderstand. It must not gain execution authority.

```text
LLM Intelligence ≠ Execution Authority
Proposal ≠ Authority
Decision Permission ≠ Execution Permission
```

`ReferenceRuntime` remains the trust boundary and Source of Truth for decision and execution control. AI and databases are replaceable surrounds.

## Target architecture (future)

```text
User
 ↓
Local ASR          （future）
 ↓
Local Small LLM
 ↓
Proposal
 ↓
Controlled Agent Runtime
 ↓
Policy / Authority / Guards
 ↓
Mock / Sandbox / Real Adapter（later Gates）
 ↓
Evidence
 ↓
Local TTS          （future）
```

## Architecture evolution

```text
Current (G1 Slice 1–2)

Human UI
   ↓
FastAPI (local demo)
   ↓
ReferenceRuntime
   ↓
Mock Adapter
   ↓
Evidence UI


Next (candidate G1 Slice 3)

Human / Text Input
   ↓
Local Small LLM
   ↓ Proposal
ReferenceRuntime
   ↓
Mock Adapter
   ↓
Evidence UI


Later

Voice
 ↓
Local ASR
 ↓
Local Small LLM
 ↓ Proposal
Controlled Runtime
 ↙          ↘
Policy      Docker DB
 ↓
HITL / Adapter
 ↓
Evidence
 ↓
Local TTS
```

## Local small LLM role

Local small models are preferred for the proposal layer.

Rough target class (not a frozen model):

- about **1.5B–4B** parameters
- Chinese understanding, slot extraction, structured output
- **replaceable**; model capability is never a safety premise

### May do

- natural-language understanding
- intent extraction
- slot extraction
- bounded clarification
- strict Proposal JSON generation
- human-readable explanation

### Must not do

- authenticated identity (`principal_id` / `tenant_id` / `application_id`)
- authoritative transaction facts
- policy decision
- approval
- idempotency authority
- execution token
- adapter result
- final execution authority

Contract:

```text
LLM → Proposal only
Runtime → Authority / Decision / Execution control
```

Do not bind docs to a specific model name or vendor. Future local and cloud providers must share the same Proposal contract.

## Future provider boundary (direction only)

Not implemented now. Recorded as architecture intent:

```text
LLMProvider
  → propose(text) -> ProposalDraft

ASRProvider
  → transcribe(audio) -> text

TTSProvider
  → synthesize(text) -> audio
```

Runtime must not depend on a specific LLM SDK.

## Local ASR / TTS

Later priority: **local ASR** and **local TTS** for offline demo, privacy, on-prem story, and replaceable providers.

Suggested phasing:

```text
G1 Slice 3   Local LLM Proposal Layer
Later        Local ASR
Later        Local TTS
```

ASR/TTS technology choice is **not frozen**.

## Database direction

Future persistence prefers:

```text
Docker
 └── Database
```

**Technology candidate (not frozen):** PostgreSQL in Docker.

Why it is a candidate:

- convenient local development
- open source
- mature transactions / concurrency
- JSON support
- closer to a real service shape than SQLite for audit/query

### Serves

- execution cases
- evidence persistence
- idempotency
- human-review cases
- policy/version references
- later audit/query

### Must never become

- LLM authority
- policy bypass
- approval shortcut

### Gate mapping

```text
G2 candidate:
Local Docker PostgreSQL reference persistence
```

This roadmap does **not** add dependencies, docker-compose, schemas, or migrations.

## LangChain / LangGraph / Langfuse

Not required now.

| Framework | Position |
|---|---|
| LangGraph | Evaluate only when true multi-step agent workflow / state orchestration is needed |
| Langfuse | Evaluate when model tracing / eval / observability demand is mature |
| LangChain | Optional integration aid only if it clearly reduces complexity |

Principle:

> Framework is replaceable.  
> Controlled Runtime is the trust boundary.

Do not introduce frameworks for stack completeness.

## Suggested next Gate slice

After this roadmap is accepted:

> **G1 Slice 3 — Local Small LLM Proposal Layer**

Still behind Runtime. Still synthetic / mock adapters unless separately authorized.

## Related open questions

See `docs/inception/06-open-questions.md` OQ-12 … OQ-21.
