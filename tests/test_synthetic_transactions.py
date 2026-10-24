from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.demo.synthetic_transactions import (
    AuthoritativeLookupError,
    IndexedTransaction,
    SyntheticTransactionRepository,
    build_seed_from_authoritative_lookup,
)


class SyntheticTransactionRepositoryTests(unittest.TestCase):
    def test_indexes_three_demo_seeds(self) -> None:
        repo = SyntheticTransactionRepository.from_demo_seeds()
        orders = {row.original_order_no for row in repo.records}
        self.assertEqual(
            orders, {"order_demo_001", "order_demo_002", "order_demo_003"}
        )

    def test_lookup_001_keeps_seed_01_facts(self) -> None:
        seed = build_seed_from_authoritative_lookup(
            {
                "intent": "refund",
                "appid": "app_demo_001",
                "original_order_no": "order_demo_001",
                "requested_amount_minor": 10000,
            }
        )
        self.assertEqual(seed["seed_id"], "seed-01")
        self.assertEqual(
            seed["tool_fixtures"]["transaction_query_tool"]["resource_ref"],
            "txn_demo_001",
        )
        self.assertEqual(
            seed["tool_fixtures"]["transaction_query_tool"]["original_amount_minor"],
            10000,
        )
        self.assertEqual(
            seed["trusted_context"]["principal_id"], "principal_demo_001"
        )
        self.assertNotIn("scenario", seed)

    def test_lookup_002_keeps_seed_02_facts(self) -> None:
        seed = build_seed_from_authoritative_lookup(
            {
                "intent": "refund",
                "appid": "app_demo_001",
                "original_order_no": "order_demo_002",
                "requested_amount_minor": 10001,
            }
        )
        self.assertEqual(seed["seed_id"], "seed-02")
        self.assertEqual(
            seed["tool_fixtures"]["transaction_query_tool"]["resource_ref"],
            "txn_demo_002",
        )
        self.assertEqual(
            seed["tool_fixtures"]["transaction_query_tool"]["original_amount_minor"],
            10001,
        )

    def test_unknown_order_raises_unavailable(self) -> None:
        with self.assertRaises(AuthoritativeLookupError) as ctx:
            build_seed_from_authoritative_lookup(
                {
                    "appid": "app_demo_001",
                    "original_order_no": "order_demo_999",
                    "requested_amount_minor": 10000,
                }
            )
        self.assertEqual(ctx.exception.reason_code, "authoritative_facts_unavailable")

    def test_appid_mismatch_raises_mismatch(self) -> None:
        with self.assertRaises(AuthoritativeLookupError) as ctx:
            build_seed_from_authoritative_lookup(
                {
                    "appid": "app_other_001",
                    "original_order_no": "order_demo_001",
                }
            )
        self.assertEqual(ctx.exception.reason_code, "authoritative_lookup_mismatch")

    def test_term_id_mismatch_raises_mismatch(self) -> None:
        with self.assertRaises(AuthoritativeLookupError) as ctx:
            build_seed_from_authoritative_lookup(
                {
                    "appid": "app_demo_001",
                    "original_order_no": "order_demo_001",
                    "term_id": "term_demo_002",
                }
            )
        self.assertEqual(ctx.exception.reason_code, "authoritative_lookup_mismatch")

    def test_ambiguous_multi_match_never_auto_picks(self) -> None:
        base = SyntheticTransactionRepository.from_demo_seeds().records[0]
        clone = IndexedTransaction(
            original_order_no=base.original_order_no,
            appid=base.appid,
            term_id="term_dup",
            original_transaction_date=base.original_transaction_date,
            seed=copy.deepcopy(base.seed),
        )
        repo = SyntheticTransactionRepository((base, clone))
        with self.assertRaises(AuthoritativeLookupError) as ctx:
            repo.lookup(
                {
                    "appid": base.appid,
                    "original_order_no": base.original_order_no,
                }
            )
        self.assertEqual(ctx.exception.reason_code, "authoritative_lookup_ambiguous")


if __name__ == "__main__":
    unittest.main()
