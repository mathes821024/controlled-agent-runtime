# G1 Slice 2 — Human Acceptance UI × ReferenceRuntime

**Branch:** `feat/g1-human-runtime-ui`  
**Mode:** synthetic only · real adapters disabled · local only

## Start

```bash
make demo
```

Open:

```text
http://127.0.0.1:8000
```

Requires a local `.venv` with optional extras:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[demo]'
```

## Architecture

```text
Browser UI (docs/ui/prototype/index.html)
        ↓  POST /api/demo/run
Local FastAPI bridge
        ↓
ReferenceRuntime.run_seed(...)
        ↓
outcome / reason / adapter_call_count / evidence
```

Frontend does not decide outcomes. Static scenario text is display metadata only.

## Scenarios

| UI | API | Source |
|---|---|---|
| 安全自动通过 | `safe_auto` | refund-seed-01 |
| 需要人工审核 | `human_review` | refund-seed-02 |
| 金额不一致 | `amount_mismatch` | refund-seed-03 |
| 伪造身份 | `authority_attack` | seed-01 + forged `principal_id` |
