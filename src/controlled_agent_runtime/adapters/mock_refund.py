"""Synthetic mock refund adapter only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class MockAdapterRequest:
    resource_ref: str
    refund_amount_minor: int
    currency: str
    original_order_no: str
    appid: str
    execution_token: str


@dataclass(frozen=True)
class MockAdapterResponse:
    transport_status: str
    protocol_status: str
    schema_status: str
    respCode: str
    normalized_business_result: str
    business_status: str


class MockRefundAdapter:
    """Returns fixture-driven synthetic results. Never talks to production."""

    def __init__(self, fixture: Optional[Mapping[str, Any]] = None) -> None:
        self._fixture = dict(fixture or {})
        self.call_count = 0
        self.last_request: Optional[MockAdapterRequest] = None

    def execute(self, request: MockAdapterRequest) -> MockAdapterResponse:
        self.call_count += 1
        self.last_request = request
        fx = self._fixture
        resp_code = str(fx.get("respCode", "00"))
        normalized = str(
            fx.get("normalized_business_result")
            or _normalize_resp_code(resp_code)
        )
        return MockAdapterResponse(
            transport_status=str(fx.get("transport_status", "success")),
            protocol_status=str(fx.get("protocol_status", "success")),
            schema_status=str(fx.get("schema_status", "success")),
            respCode=resp_code,
            normalized_business_result=normalized,
            business_status=str(fx.get("business_status", "success")),
        )


def _normalize_resp_code(resp_code: str) -> str:
    if resp_code == "00":
        return "REFUND_SUCCEEDED"
    if resp_code == "12":
        return "ALREADY_REFUNDED"
    return "REFUND_FAILED"
