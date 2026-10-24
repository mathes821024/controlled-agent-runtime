"""Synthetic authoritative transaction lookup for proposal-only ingress.

Indexed from ``demo-seeds/refund-seed-0{1,2,3}.json``. Not a real database.
Runtime / policy / HITL stay unchanged: this module only chooses which seed's
trusted_context and tool_fixtures bind to a sanitized proposal.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[3]
SEED_FILES = (
    "refund-seed-01.json",
    "refund-seed-02.json",
    "refund-seed-03.json",
)
REQUIRED_LOCATOR_KEYS = ("original_order_no", "appid")
OPTIONAL_LOCATOR_KEYS = ("term_id", "original_transaction_date")


class AuthoritativeLookupError(ValueError):
    """Typed fail-closed lookup error; ``reason_code`` is stable for tests."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class IndexedTransaction:
    original_order_no: str
    appid: str
    term_id: str
    original_transaction_date: str
    seed: dict[str, Any]


def _load_seed(filename: str) -> dict[str, Any]:
    path = ROOT / "demo-seeds" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def _index_seed(seed: Mapping[str, Any]) -> IndexedTransaction:
    proposal = seed.get("proposal") if isinstance(seed.get("proposal"), Mapping) else {}
    return IndexedTransaction(
        original_order_no=str(proposal.get("original_order_no") or "").strip(),
        appid=str(proposal.get("appid") or "").strip(),
        term_id=str(proposal.get("term_id") or "").strip(),
        original_transaction_date=str(
            proposal.get("original_transaction_date") or ""
        ).strip(),
        seed=copy.deepcopy(dict(seed)),
    )


class SyntheticTransactionRepository:
    """In-memory index of synthetic refund seeds."""

    def __init__(self, records: Iterable[IndexedTransaction] | None = None) -> None:
        if records is None:
            self._records = tuple(_index_seed(_load_seed(name)) for name in SEED_FILES)
        else:
            self._records = tuple(records)

    @classmethod
    def from_demo_seeds(cls) -> SyntheticTransactionRepository:
        return cls()

    @property
    def records(self) -> tuple[IndexedTransaction, ...]:
        return self._records

    def lookup(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        """Return a Runtime seed bound to the authoritative resource.

        Required keys: ``original_order_no`` + ``appid``. Optional ``term_id``
        and ``original_transaction_date`` must match when present.
        """
        if not isinstance(proposal, Mapping):
            raise AuthoritativeLookupError("authoritative_facts_unavailable")
        order = str(proposal.get("original_order_no") or "").strip()
        appid = str(proposal.get("appid") or "").strip()
        if not order or not appid:
            raise AuthoritativeLookupError("authoritative_facts_unavailable")

        by_order = [row for row in self._records if row.original_order_no == order]
        if not by_order:
            raise AuthoritativeLookupError("authoritative_facts_unavailable")

        matched = [row for row in by_order if row.appid == appid]
        if not matched:
            raise AuthoritativeLookupError("authoritative_lookup_mismatch")

        term_id = str(proposal.get("term_id") or "").strip()
        if term_id:
            term_hits = [row for row in matched if row.term_id == term_id]
            if not term_hits:
                raise AuthoritativeLookupError("authoritative_lookup_mismatch")
            matched = term_hits

        txn_date = str(proposal.get("original_transaction_date") or "").strip()
        if txn_date:
            date_hits = [
                row for row in matched if row.original_transaction_date == txn_date
            ]
            if not date_hits:
                raise AuthoritativeLookupError("authoritative_lookup_mismatch")
            matched = date_hits

        if len(matched) > 1:
            raise AuthoritativeLookupError("authoritative_lookup_ambiguous")

        return bind_authoritative_seed(matched[0], proposal)


def bind_authoritative_seed(
    record: IndexedTransaction,
    sanitized_proposal: Mapping[str, Any],
) -> dict[str, Any]:
    """Trusted facts from the looked-up seed; proposal overlay is untrusted."""
    seed = copy.deepcopy(record.seed)
    seed["proposal"] = dict(sanitized_proposal)
    return seed


def build_seed_from_authoritative_lookup(
    sanitized_proposal: Mapping[str, Any],
    repository: SyntheticTransactionRepository | None = None,
) -> dict[str, Any]:
    repo = repository if repository is not None else SyntheticTransactionRepository()
    return repo.lookup(sanitized_proposal)
