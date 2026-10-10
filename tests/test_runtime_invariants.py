from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.models import RuntimeOutcome
from controlled_agent_runtime.runtime import ReferenceRuntime
from seed_helpers import load_seed


class RuntimeInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = load_seed("refund-seed-01.json")

    def _run(self, seed: dict):
        return ReferenceRuntime().run_seed(seed)

    def test_forged_principal_id_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["proposal"]["principal_id"] = "forged"
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("principal_id", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", result.event_names())

    def test_forged_application_id_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["proposal"]["application_id"] = "forged"
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("application_id", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)

    def test_forged_original_amount_minor_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["proposal"]["original_amount_minor"] = 1
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("original_amount_minor", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)

    def test_forged_approval_status_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["proposal"]["approval_status"] = "approved"
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("approval_status", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)

    def test_amount_mismatch_never_calls_adapter(self) -> None:
        seed = load_seed("refund-seed-03.json")
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.DENIED)
        self.assertEqual(result.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", result.event_names())

    def test_above_threshold_never_calls_adapter(self) -> None:
        seed = load_seed("refund-seed-02.json")
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.NEEDS_REVIEW)
        self.assertEqual(result.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", result.event_names())

    def test_duplicate_execution_does_not_call_adapter_twice(self) -> None:
        seed = load_seed("refund-seed-01.json")
        runtime = ReferenceRuntime()
        first = runtime.run_seed(seed)
        second = runtime.run_seed(seed)
        self.assertEqual(first.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(first.adapter_call_count, 1)
        self.assertEqual(second.outcome, RuntimeOutcome.IDEMPOTENT_REPLAY)
        self.assertEqual(second.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", second.event_names())

    def test_missing_authoritative_facts_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["transaction_query_tool"] = {"found": False}
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertEqual(result.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", result.event_names())

    def test_unknown_resp_code_never_promoted_to_success(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "success",
            "respCode": "99",
            "normalized_business_result": "REFUND_FAILED",
            "business_status": "failed",
        }
        result = self._run(seed)
        self.assertNotEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.resp_code, "99")
        self.assertEqual(result.normalized_business_result, "REFUND_FAILED")

    def test_transport_success_is_not_business_success(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "success",
            "respCode": "12",
            "normalized_business_result": "ALREADY_REFUNDED",
            "business_status": "already_refunded",
        }
        result = self._run(seed)
        self.assertNotEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.normalized_business_result, "ALREADY_REFUNDED")
        self.assertEqual(result.reason_code, "already_refunded_outcome_unmapped")

    def test_appid_allowed_application_id_forbidden(self) -> None:
        seed = copy.deepcopy(self.base)
        # appid remains allowed business locator
        self.assertIn("appid", seed["proposal"])
        ok = self._run(seed)
        self.assertEqual(ok.outcome, RuntimeOutcome.EXECUTED)
        seed2 = copy.deepcopy(self.base)
        seed2["proposal"]["application_id"] = seed2["trusted_context"]["application_id"]
        bad = self._run(seed2)
        self.assertEqual(bad.outcome, RuntimeOutcome.FAILED_CLOSED)



    def test_missing_mock_adapter_fixture_never_executes(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"].pop("mock_refund_adapter", None)
        result = self._run(seed)
        self.assertNotEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("mock_adapter_fixture", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)
        self.assertNotIn("mock_adapter_called", result.event_names())
        self.assertNotIn("refund_succeeded", result.event_names())

    def test_schema_failure_never_executed_even_if_respcode_00(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "failed",
            "respCode": "00",
            "normalized_business_result": "REFUND_SUCCEEDED",
            "business_status": "success",
        }
        result = self._run(seed)
        self.assertNotEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)

    def test_business_status_failure_never_executed_even_if_respcode_00(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "success",
            "respCode": "00",
            "normalized_business_result": "REFUND_SUCCEEDED",
            "business_status": "failed",
        }
        result = self._run(seed)
        self.assertNotEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)

    def test_failed_execution_retry_is_not_success_replay(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "success",
            "respCode": "99",
            "normalized_business_result": "REFUND_FAILED",
            "business_status": "failed",
        }
        runtime = ReferenceRuntime()
        first = runtime.run_seed(seed)
        self.assertEqual(first.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertEqual(first.resp_code, "99")
        second = runtime.run_seed(seed)
        self.assertNotEqual(second.outcome, RuntimeOutcome.IDEMPOTENT_REPLAY)
        self.assertNotEqual(second.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(second.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertEqual(second.resp_code, "99")

    def test_already_refunded_retry_is_not_success_replay(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["mock_refund_adapter"] = {
            "transport_status": "success",
            "protocol_status": "success",
            "schema_status": "success",
            "respCode": "12",
            "normalized_business_result": "ALREADY_REFUNDED",
            "business_status": "already_refunded",
        }
        runtime = ReferenceRuntime()
        first = runtime.run_seed(seed)
        self.assertEqual(first.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertEqual(first.normalized_business_result, "ALREADY_REFUNDED")
        second = runtime.run_seed(seed)
        self.assertNotEqual(second.outcome, RuntimeOutcome.IDEMPOTENT_REPLAY)
        self.assertNotEqual(second.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(second.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertEqual(second.normalized_business_result, "ALREADY_REFUNDED")

    def test_non_cny_currency_fail_closed(self) -> None:
        seed = copy.deepcopy(self.base)
        seed["tool_fixtures"]["transaction_query_tool"]["currency"] = "USD"
        result = self._run(seed)
        self.assertEqual(result.outcome, RuntimeOutcome.FAILED_CLOSED)
        self.assertIn("currency", result.reason_code)
        self.assertEqual(result.adapter_call_count, 0)

if __name__ == "__main__":
    unittest.main()
