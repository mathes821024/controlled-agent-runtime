"""Map demo scenarios to synthetic seeds / attack inputs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

SCENARIO_ALIASES = {
    "safe_auto": "safe_auto",
    "safe": "safe_auto",
    "human_review": "human_review",
    "review": "human_review",
    "amount_mismatch": "amount_mismatch",
    "mismatch": "amount_mismatch",
    "authority_attack": "authority_attack",
    "attack": "authority_attack",
}

EVENT_STATION = {
    "proposal_received": "proposal",
    "proposal_validated": "proposal",
    "trusted_context_bound": "authority",
    "authoritative_facts_loaded": "authority",
    "policy_decided": "policy",
    "state_revalidated": "guard",
    "idempotency_reserved": "guard",
    "idempotency_hit": "guard",
    "idempotency_conflict": "guard",
    "mock_adapter_called": "adapter",
    "result_normalized": "adapter",
    "trace_completed": "adapter",
}

EVENT_COPY = {
    "proposal_received": ("提案已收下，准备校验。", "Proposal accepted for validation."),
    "proposal_validated": ("提案字段允许使用。", "Proposal fields are allowed."),
    "trusted_context_bound": ("已绑定经过认证的身份。", "Authenticated context bound."),
    "authoritative_facts_loaded": ("已装入权威交易事实。", "Authoritative transaction facts loaded."),
    "policy_decided": ("策略已给出决定。", "Policy decision recorded."),
    "state_revalidated": ("执行前再次确认，守卫仍然成立。", "Guards still hold before any side effect."),
    "idempotency_reserved": ("已在内存中占用幂等。", "In-memory reservation placed."),
    "idempotency_hit": ("命中已完成的幂等结果，未再次调用适配器。", "Completed idempotency hit; adapter not called again."),
    "idempotency_conflict": ("幂等冲突，安全停止。", "Idempotency conflict; fail closed."),
    "mock_adapter_called": ("已调用模拟适配器。", "Mock adapter called."),
    "result_normalized": ("结果已归一化。", "Result normalized."),
    "trace_completed": ("证据到此结束。", "Trace closed."),
}

OUTCOME_UI = {
    "executed": {
        "tone": "executed",
        "outcome_zh": "已执行",
        "outcome_en": "EXECUTED",
        "why_zh": "守卫通过后，模拟适配器被调用。结论来自 ReferenceRuntime，不是前端写死。",
        "why_en": "Guards passed and the mock adapter ran. This outcome comes from ReferenceRuntime.",
    },
    "needs_review": {
        "tone": "review",
        "outcome_zh": "需要人工审核",
        "outcome_en": "NEEDS REVIEW",
        "why_zh": "策略要求人工审核。没有调用适配器，也没有伪造批准。",
        "why_en": "Policy requires human review. No adapter call and no invented approval.",
    },
    "denied": {
        "tone": "denied",
        "outcome_zh": "已拒绝",
        "outcome_en": "DENIED",
        "why_zh": "策略拒绝了这次提案。没有调用适配器。",
        "why_en": "Policy denied the proposal. No adapter was called.",
    },
    "failed_closed": {
        "tone": "closed",
        "outcome_zh": "已安全停止",
        "outcome_en": "FAILED CLOSED",
        "why_zh": "依赖缺失、越权字段或不可信业务结果导致 fail closed。",
        "why_en": "Missing dependency, protected-field forgery, or untrusted business proof failed closed.",
    },
    "needs_input": {
        "tone": "review",
        "outcome_zh": "需要补充输入",
        "outcome_en": "NEEDS INPUT",
        "why_zh": "提案缺必填字段。",
        "why_en": "Required proposal fields are missing.",
    },
    "idempotent_replay": {
        "tone": "executed",
        "outcome_zh": "幂等重放",
        "outcome_en": "IDEMPOTENT REPLAY",
        "why_zh": "同一动作身份已成功执行过，本次未再次调用适配器。",
        "why_en": "A completed execution already exists for this identity; adapter was not called again.",
    },
}


def normalize_scenario(name: str) -> str:
    key = (name or "").strip().lower()
    if key not in SCENARIO_ALIASES:
        raise KeyError(name)
    return SCENARIO_ALIASES[key]


def _load_seed(filename: str) -> dict[str, Any]:
    path = ROOT / "demo-seeds" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def build_seed_for_scenario(scenario: str) -> dict[str, Any]:
    canonical = normalize_scenario(scenario)
    if canonical == "safe_auto":
        return _load_seed("refund-seed-01.json")
    if canonical == "human_review":
        return _load_seed("refund-seed-02.json")
    if canonical == "amount_mismatch":
        return _load_seed("refund-seed-03.json")
    if canonical == "authority_attack":
        seed = copy.deepcopy(_load_seed("refund-seed-01.json"))
        seed["proposal"] = dict(seed["proposal"])
        seed["proposal"]["principal_id"] = "forged"
        seed["seed_id"] = "authority-attack"
        return seed
    raise KeyError(scenario)


def build_proposal_template_seed(sanitized_proposal: dict[str, Any]) -> dict[str, Any]:
    """Trusted facts from refund-seed-01 plus an untrusted proposal overlay.

    Used when Ingress receives a non-empty proposal and no canned scenario.
    Does not invent a scenario name as authority. Runtime / policy decide.
    """
    seed = copy.deepcopy(_load_seed("refund-seed-01.json"))
    seed["proposal"] = dict(sanitized_proposal)
    return seed


def station_for_event(name: str, fallback: str = "adapter") -> str:
    return EVENT_STATION.get(name, fallback)


def enrich_evidence(events: list[Any], reason_code: str) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    last_station = "proposal"
    for event in events:
        name = event.name
        station = station_for_event(name, last_station)
        if name != "trace_completed":
            last_station = station
        else:
            station = last_station
        zh, en = EVENT_COPY.get(name, (name, name))
        summary = event.summary or ""
        reason = event.reason_code or ""
        reject = False
        if name == "proposal_validated" and reason.startswith("proposal_contains_protected"):
            zh = f"安全停止。{reason}"
            en = f"fail_closed, {reason}"
            reject = True
        elif name == "policy_decided" and reason:
            zh = f"{summary or '策略决定'}。原因 {reason}。"
            en = f"{summary or 'policy decided'}, {reason}."
        elif name == "trace_completed":
            zh = f"证据到此结束。原因是 {reason or reason_code or 'n/a'}。"
            en = f"Trace closed. Reason: {reason or reason_code or 'n/a'}."
        elif name == "mock_adapter_called" and summary:
            zh = f"模拟适配器：{summary}"
            en = f"Mock adapter: {summary}"
        elif name == "result_normalized" and summary:
            zh = f"归一化结果：{summary}"
            en = f"Normalized: {summary}"
        item = {
            "name": name,
            "sequence": event.sequence,
            "station": station,
            "zh": zh,
            "en": en,
            "summary": summary,
            "reason_code": reason,
        }
        if reject:
            item["reject"] = True
        enriched.append(item)
    return enriched


def stop_station_from_evidence(evidence: list[dict[str, Any]], outcome: str) -> str:
    if outcome == "executed":
        return ""
    names = [item["name"] for item in evidence]
    if "policy_decided" in names and "state_revalidated" not in names:
        return "policy"
    if "proposal_validated" in names and "trusted_context_bound" not in names:
        return "proposal"
    if "state_revalidated" in names and "mock_adapter_called" not in names:
        return "guard"
    return "adapter"
