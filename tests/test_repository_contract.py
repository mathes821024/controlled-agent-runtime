from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.validation import (
    HITL_THRESHOLD_EXCLUSIVE_MINOR,
    PROTECTED_FIELDS,
    validate_repository,
)


class RepositoryContractTests(unittest.TestCase):
    def test_repository_validation_passes(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_policy_protects_privileged_fields(self) -> None:
        policy = json.loads(
            (ROOT / "policy/examples/refund-demo-policy.json").read_text(encoding="utf-8")
        )
        forbidden = set(policy["proposal"]["forbidden_fields"])
        self.assertTrue(PROTECTED_FIELDS <= forbidden)
        self.assertIn("original_amount_minor", forbidden)
        self.assertIn("refund_amount_minor", forbidden)
        self.assertIn("respCode", forbidden)

    def test_money_unit_and_hitl_threshold_contract(self) -> None:
        policy = json.loads(
            (ROOT / "policy/examples/refund-demo-policy.json").read_text(encoding="utf-8")
        )
        money = policy["money"]
        self.assertEqual(money["currency"], "CNY")
        self.assertEqual(money["representation"], "integer_minor_units")
        self.assertEqual(money["minor_units_per_major"], 100)
        self.assertEqual(money["hitl_threshold_exclusive_minor"], HITL_THRESHOLD_EXCLUSIVE_MINOR)
        self.assertIs(money["floating_amounts_allowed"], False)
        hitl = next(rule for rule in policy["rules"] if rule["rule_id"] == "R-04")
        self.assertEqual(
            hitl["when"]["proposal.requested_amount_minor_greater_than"],
            HITL_THRESHOLD_EXCLUSIVE_MINOR,
        )
        self.assertEqual(hitl["outcome"], "needs_review")

    def test_condition_language_not_frozen(self) -> None:
        policy = json.loads(
            (ROOT / "policy/examples/refund-demo-policy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["condition_language"]["status"], "NOT_FROZEN")

    def test_refund_business_result_codes(self) -> None:
        policy = json.loads(
            (ROOT / "policy/examples/refund-demo-policy.json").read_text(encoding="utf-8")
        )
        codes = policy["refund_business_results"]["codes"]
        self.assertEqual(codes["00"], "REFUND_SUCCEEDED")
        self.assertEqual(codes["12"], "ALREADY_REFUNDED")
        self.assertEqual(codes["other"], "REFUND_FAILED")

    def test_seed_01_future_conformance_boundary_case(self) -> None:
        seed = json.loads(
            (ROOT / "demo-seeds/refund-seed-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(seed["expectation_kind"], "future_conformance_expectation")
        self.assertEqual(seed["data_mode"], "synthetic_only")
        self.assertEqual(seed["proposal"]["requested_amount_minor"], 10000)
        self.assertEqual(
            seed["tool_fixtures"]["transaction_query_tool"]["original_amount_minor"],
            10000,
        )
        self.assertEqual(seed["expected"]["adapter_call_count"], 1)
        self.assertIn("mock_adapter_called", seed["expected"]["required_event_order"])
        self.assertIn("real_adapter_called", seed["expected"]["forbidden_events"])
        self.assertEqual(
            seed["tool_fixtures"]["mock_refund_adapter"]["respCode"],
            "00",
        )

    def test_seed_02_above_threshold_requires_review_without_execution(self) -> None:
        seed = json.loads(
            (ROOT / "demo-seeds/refund-seed-02.json").read_text(encoding="utf-8")
        )
        self.assertEqual(seed["expectation_kind"], "future_conformance_expectation")
        self.assertGreater(seed["proposal"]["requested_amount_minor"], 10000)
        self.assertEqual(seed["expected"]["outcome"], "needs_review")
        self.assertEqual(seed["expected"]["adapter_call_count"], 0)
        forbidden = set(seed["expected"]["forbidden_events"])
        self.assertTrue(
            {"mock_adapter_called", "real_adapter_called", "refund_succeeded"}
            <= forbidden
        )

    def test_seed_03_amount_mismatch_denies_without_execution(self) -> None:
        seed = json.loads(
            (ROOT / "demo-seeds/refund-seed-03.json").read_text(encoding="utf-8")
        )
        proposal_amount = seed["proposal"]["requested_amount_minor"]
        authoritative = seed["tool_fixtures"]["transaction_query_tool"][
            "original_amount_minor"
        ]
        self.assertNotEqual(proposal_amount, authoritative)
        self.assertEqual(seed["expected"]["outcome"], "denied")
        self.assertEqual(seed["expected"]["reason_code"], "full_refund_only")
        self.assertEqual(seed["expected"]["adapter_call_count"], 0)
        forbidden = set(seed["expected"]["forbidden_events"])
        self.assertTrue(
            {"mock_adapter_called", "real_adapter_called", "refund_succeeded"}
            <= forbidden
        )


if __name__ == "__main__":
    unittest.main()
