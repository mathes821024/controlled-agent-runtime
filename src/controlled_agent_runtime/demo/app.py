"""FastAPI bridge: Human Acceptance UI → ReferenceRuntime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from controlled_agent_runtime.demo.scenarios import (
    OUTCOME_UI,
    build_seed_for_scenario,
    enrich_evidence,
    normalize_scenario,
    stop_station_from_evidence,
)
from controlled_agent_runtime.proposal_hook import (
    ProposalHookError,
    resolve_proposal_hook_mode,
    run_proposal_hook,
)
from controlled_agent_runtime.runtime import ReferenceRuntime

ROOT = Path(__file__).resolve().parents[3]
UI_DIR = ROOT / "docs" / "ui" / "prototype"


class RunRequest(BaseModel):
    scenario: str = Field(..., min_length=1, max_length=64)


class ProposeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


def serialize_result(scenario: str, result: Any) -> dict[str, Any]:
    decision = None
    if result.decision is not None:
        decision = {
            "outcome": result.decision.outcome.value,
            "reason_code": result.decision.reason_code,
            "rule_id": result.decision.rule_id,
        }
    evidence = enrich_evidence(result.evidence, result.reason_code)
    outcome = result.outcome.value
    ui = dict(OUTCOME_UI.get(outcome, OUTCOME_UI["failed_closed"]))
    return {
        "scenario": scenario,
        "outcome": outcome,
        "reason_code": result.reason_code,
        "adapter_call_count": result.adapter_call_count,
        "decision": decision,
        "normalized_business_result": result.normalized_business_result,
        "resp_code": result.resp_code,
        "summary": result.summary,
        "evidence": evidence,
        "ui": {
            **ui,
            "stop_station": stop_station_from_evidence(evidence, outcome),
            "source": "ReferenceRuntime",
        },
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="Controlled Agent Runtime — Human Acceptance Demo",
        version="0.1.0-g1-slice2",
        docs_url="/api/docs",
        redoc_url=None,
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        hook = "off"
        try:
            hook = resolve_proposal_hook_mode()
        except ProposalHookError as exc:
            hook = exc.reason_code
        return {
            "status": "ok",
            "mode": "synthetic_only",
            "real_adapters": "disabled",
            "proposal_hook": hook,
            "llm": "disabled",
        }

    @app.post("/api/demo/propose")
    def propose(body: ProposeRequest) -> Any:
        result = run_proposal_hook(body.text)
        status = 409
        if result.reason_code.startswith("unknown_proposal_hook_mode"):
            status = 400
        elif result.reason_code == "local_model_unavailable_no_download":
            status = 503
        return JSONResponse(
            status_code=status,
            content={
                "outcome": "failed_closed",
                "reason_code": result.reason_code,
                "proposal": result.proposal,
                "hook": result.mode,
                "download_attempted": result.download_attempted,
                "message": "Proposal hook is optional and offline by default.",
            },
        )

    @app.post("/api/demo/run")
    def run_demo(body: RunRequest) -> Any:
        try:
            canonical = normalize_scenario(body.scenario)
        except KeyError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "outcome": "failed_closed",
                    "reason_code": "unknown_scenario",
                    "adapter_call_count": 0,
                    "message": f"unknown scenario: {body.scenario}",
                },
            ) from exc
        try:
            seed = build_seed_for_scenario(canonical)
            local = ReferenceRuntime()
            result = local.run_seed(seed)
            return serialize_result(canonical, result)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content={
                    "scenario": canonical,
                    "outcome": "failed_closed",
                    "reason_code": f"runtime_exception:{type(exc).__name__}",
                    "adapter_call_count": 0,
                    "decision": None,
                    "normalized_business_result": None,
                    "resp_code": None,
                    "summary": "Runtime unavailable or failed closed",
                    "evidence": [],
                    "ui": {
                        **OUTCOME_UI["failed_closed"],
                        "outcome_zh": "运行时不可用",
                        "outcome_en": "RUNTIME UNAVAILABLE",
                        "why_zh": "本地 Runtime 出错。没有展示预设成功结果。",
                        "why_en": "Local runtime failed. No canned success is shown.",
                        "stop_station": "proposal",
                        "source": "error",
                    },
                    "error": type(exc).__name__,
                },
            )

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(UI_DIR / "index.html")

    if UI_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "outcome": "failed_closed",
                "reason_code": f"api_exception:{type(exc).__name__}",
                "adapter_call_count": 0,
                "message": "API fail closed",
            },
        )

    return app
