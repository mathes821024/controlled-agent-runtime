"""Ordered evidence trace helpers."""

from __future__ import annotations

from .models import EvidenceEvent


class EvidenceTrace:
    def __init__(self) -> None:
        self._events: list[EvidenceEvent] = []

    def record(self, name: str, summary: str = "", reason_code: str = "") -> None:
        self._events.append(
            EvidenceEvent(
                name=name,
                sequence=len(self._events) + 1,
                summary=summary,
                reason_code=reason_code,
            )
        )

    @property
    def events(self) -> list[EvidenceEvent]:
        return list(self._events)

    def names(self) -> list[str]:
        return [e.name for e in self._events]
