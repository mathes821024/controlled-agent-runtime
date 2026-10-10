"""In-memory idempotency store for Gate 1 reference runtime.

This is NOT a production idempotency key design (OQ-10 remains open).
Keys are structured runtime tuples for tests only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .models import RuntimeResult


@dataclass(frozen=True)
class IdempotencyIdentity:
    """Test-only structured action identity. Not final production key format."""

    tenant_id: str
    application_id: str
    principal_id: str
    resource_ref: str
    original_order_no: str
    appid: str
    refund_amount_minor: int

    def key(self) -> tuple[Any, ...]:
        return (
            self.tenant_id,
            self.application_id,
            self.principal_id,
            self.resource_ref,
            self.original_order_no,
            self.appid,
            self.refund_amount_minor,
        )


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._reserved: dict[tuple[Any, ...], RuntimeResult] = {}

    def get(self, identity: IdempotencyIdentity) -> Optional[RuntimeResult]:
        return self._reserved.get(identity.key())

    def reserve(self, identity: IdempotencyIdentity, placeholder: RuntimeResult) -> bool:
        """Return True if newly reserved; False if already present."""
        key = identity.key()
        if key in self._reserved:
            return False
        self._reserved[key] = placeholder
        return True

    def complete(self, identity: IdempotencyIdentity, result: RuntimeResult) -> None:
        self._reserved[identity.key()] = result
