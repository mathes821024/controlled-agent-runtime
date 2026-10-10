"""Synthetic mock refund adapter only.

Missing or incomplete fixture must fail closed — never success-by-default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

REQUIRED_FIXTURE_FIELDS = (
    "transport_status",
    "protocol_status",
    "schema_status",
    "respCode",
    "normalized_business_result",
    "business_status",
)


class MockAdapterUnavailableError(ValueError):
    """Raised when mock adapter dependency is missing or malformed."""


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


def require_mock_fixture(fixture: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    if fixture is None or not isinstance(fixture, Mapping) or len(fixture) == 0:
        raise MockAdapterUnavailableError("mock_adapter_fixture_missing")
    missing = [name for name in REQUIRED_FIXTURE_FIELDS if name not in fixture]
    if missing:
        raise MockAdapterUnavailableError(
            "mock_adapter_fixture_incomplete:" + ",".join(missing)
        )
    # No success defaults: every required field must be present as provided.
    return {
        "transport_status": str(fixture["transport_status"]),
        "protocol_status": str(fixture["protocol_status"]),
        "schema_status": str(fixture["schema_status"]),
        "respCode": str(fixture["respCode"]),
        "normalized_business_result": str(fixture["normalized_business_result"]),
        "business_status": str(fixture["business_status"]),
    }


class MockRefundAdapter:
    """Returns fixture-driven synthetic results. Never talks to production."""

    def __init__(self, fixture: Mapping[str, Any]) -> None:
        self._fixture = require_mock_fixture(fixture)
        self.call_count = 0
        self.last_request: Optional[MockAdapterRequest] = None

    def execute(self, request: MockAdapterRequest) -> MockAdapterResponse:
        self.call_count += 1
        self.last_request = request
        fx = self._fixture
        return MockAdapterResponse(
            transport_status=fx["transport_status"],
            protocol_status=fx["protocol_status"],
            schema_status=fx["schema_status"],
            respCode=fx["respCode"],
            normalized_business_result=fx["normalized_business_result"],
            business_status=fx["business_status"],
        )
