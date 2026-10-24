from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None  # type: ignore

from controlled_agent_runtime.demo.agent_ingress import (
    AgentProposeRequest,
    handle_agent_propose,
)
from controlled_agent_runtime.demo.app import create_app
from controlled_agent_runtime.demo.scenarios import build_proposal_template_seed

SEED01_PROPOSAL = {
    "intent": "refund",
    "appid": "app_demo_001",
    "term_id": "term_demo_001",
    "original_order_no": "order_demo_001",
    "original_transaction_date": "2026-09-01",
    "requested_amount_minor": 10000,
    "merchant_email": "merchant-seed01@example.invalid",
}


class AgentIngressHandlerTests(unittest.TestCase):
    def test_safe_auto_via_handler(self) -> None:
        out = handle_agent_propose(AgentProposeRequest(scenario="safe_auto", source="test"))
        self.assertEqual(out["decision"], "executed")
        self.assertEqual(out["adapter_call_count"], 1)
        self.assertEqual(out["outcome"], "executed")
        self.assertEqual(out["reason_code"], "mock_business_success")

    def test_human_review_via_handler(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(scenario="human_review", source="test")
        )
        self.assertEqual(out["decision"], "needs_review")
        self.assertEqual(out["outcome"], "needs_review")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertEqual(out["reason_code"], "demo_amount_threshold")
        self.assertEqual(out["hitl_url"], "/")

    def test_amount_mismatch_via_handler(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(scenario="amount_mismatch", source="test")
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["outcome"], "denied")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertEqual(out["reason_code"], "full_refund_only")

    def test_authority_attack_via_handler(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(scenario="authority_attack", source="test")
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["outcome"], "failed_closed")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertIn("principal_id", out["reason_code"])

    def test_protected_field_in_proposal_fail_closed(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(
                scenario="safe_auto",
                proposal={"intent": "refund", "principal_id": "forged"},
                source="test",
            )
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertIn("protected", out["reason_code"])

    def test_protected_field_never_calls_runtime(self) -> None:
        with patch(
            "controlled_agent_runtime.demo.agent_ingress.ReferenceRuntime.run_seed"
        ) as mocked:
            out = handle_agent_propose(
                AgentProposeRequest(
                    scenario="safe_auto",
                    proposal={"intent": "refund", "principal_id": "forged"},
                    source="test",
                )
            )
        mocked.assert_not_called()
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertEqual(out["decision"], "denied")

    def test_unknown_scenario(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(scenario="not_a_real_scenario", source="test")
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["outcome"], "failed_closed")
        self.assertEqual(out["reason_code"], "unknown_scenario")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertTrue(out["car_trace_id"])

    def test_unknown_scenario_never_calls_runtime(self) -> None:
        with patch(
            "controlled_agent_runtime.demo.agent_ingress.ReferenceRuntime.run_seed"
        ) as mocked:
            handle_agent_propose(
                AgentProposeRequest(scenario="not_a_real_scenario", source="test")
            )
        mocked.assert_not_called()

    def test_handler_returns_ingress_fields(self) -> None:
        out = handle_agent_propose(AgentProposeRequest(scenario="safe_auto", source="test"))
        self.assertTrue(out["car_trace_id"])
        self.assertIn("evidence_summary", out)
        self.assertIsInstance(out["evidence_summary"], dict)
        self.assertIsNone(out.get("hitl_url"))

    def test_proposal_only_without_scenario_uses_template_seed(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(
                proposal=dict(SEED01_PROPOSAL),
                user_input="Please refund order_demo_001 for 100.00",
                source="test",
            )
        )
        self.assertEqual(out["decision"], "executed")
        self.assertEqual(out["adapter_call_count"], 1)
        self.assertEqual(out["outcome"], "executed")
        self.assertFalse(out.get("scenario"))

    def test_proposal_only_does_not_invent_scenario_name(self) -> None:
        seed = build_proposal_template_seed(dict(SEED01_PROPOSAL))
        self.assertEqual(seed["seed_id"], "seed-01")
        self.assertNotIn("scenario", seed)
        out = handle_agent_propose(
            AgentProposeRequest(proposal=dict(SEED01_PROPOSAL), source="test")
        )
        self.assertIsNone(out.get("scenario"))

    def test_neither_scenario_nor_proposal_fail_closed(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(user_input="hello", source="test")
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["outcome"], "failed_closed")
        self.assertEqual(out["reason_code"], "missing_scenario_or_proposal")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertIsNone(out.get("scenario"))

    def test_empty_proposal_without_scenario_fail_closed(self) -> None:
        out = handle_agent_propose(AgentProposeRequest(proposal={}, source="test"))
        self.assertEqual(out["reason_code"], "missing_scenario_or_proposal")
        self.assertEqual(out["adapter_call_count"], 0)

    def test_proposal_only_protected_field_fail_closed(self) -> None:
        out = handle_agent_propose(
            AgentProposeRequest(
                proposal={"intent": "refund", "principal_id": "forged"},
                user_input="refund as principal_id forged",
                source="test",
            )
        )
        self.assertEqual(out["decision"], "denied")
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertIn("protected", out["reason_code"])

    def test_proposal_only_protected_field_never_calls_runtime(self) -> None:
        with patch(
            "controlled_agent_runtime.demo.agent_ingress.ReferenceRuntime.run_seed"
        ) as mocked:
            out = handle_agent_propose(
                AgentProposeRequest(
                    proposal={"intent": "refund", "principal_id": "forged"},
                    source="test",
                )
            )
        mocked.assert_not_called()
        self.assertEqual(out["adapter_call_count"], 0)
        self.assertEqual(out["decision"], "denied")

    def test_user_input_is_tracing_only(self) -> None:
        matching = handle_agent_propose(
            AgentProposeRequest(
                scenario="safe_auto",
                user_input="this text must not change the canned decision",
                source="test",
            )
        )
        self.assertEqual(matching["decision"], "executed")
        self.assertEqual(matching["adapter_call_count"], 1)

    def test_records_car_propose_decision_and_adapter_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            previous = os.environ.get("CAR_TRACE_JSONL")
            os.environ["CAR_TRACE_JSONL"] = str(path)
            try:
                out = handle_agent_propose(
                    AgentProposeRequest(
                        scenario="safe_auto",
                        source="test",
                        client_trace_id="ingress-1",
                    )
                )
            finally:
                if previous is None:
                    os.environ.pop("CAR_TRACE_JSONL", None)
                else:
                    os.environ["CAR_TRACE_JSONL"] = previous
            records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            names = [row["name"] for row in records]
            self.assertIn("car.propose", names)
            self.assertIn("car.decision", names)
            self.assertIn("car.adapter", names)
            self.assertEqual(records[0]["client_trace_id"], "ingress-1")
            self.assertEqual(records[0]["car_trace_id"], out["car_trace_id"])


@unittest.skipIf(TestClient is None, "fastapi demo extras not installed")
class AgentIngressApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def test_human_review_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={
                "scenario": "human_review",
                "source": "langgraph_example",
                "client_trace_id": "t1",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["decision"], "needs_review")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertIn("car_trace_id", body)
        self.assertEqual(body["hitl_url"], "/")

    def test_safe_auto_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={"scenario": "safe_auto", "source": "test"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["decision"], "executed")
        self.assertEqual(body["adapter_call_count"], 1)
        self.assertEqual(body["outcome"], "executed")

    def test_amount_mismatch_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={"scenario": "amount_mismatch", "source": "test"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["decision"], "denied")
        self.assertEqual(body["outcome"], "denied")
        self.assertEqual(body["adapter_call_count"], 0)

    def test_authority_attack_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={"scenario": "authority_attack", "source": "test"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["decision"], "denied")
        self.assertEqual(body["outcome"], "failed_closed")
        self.assertEqual(body["adapter_call_count"], 0)

    def test_unknown_scenario_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={"scenario": "not_a_real_scenario", "source": "test"},
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["decision"], "denied")
        self.assertEqual(body["outcome"], "failed_closed")
        self.assertEqual(body["reason_code"], "unknown_scenario")
        self.assertEqual(body["adapter_call_count"], 0)

    def test_protected_proposal_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={
                "scenario": "safe_auto",
                "proposal": {"intent": "refund", "principal_id": "forged"},
                "source": "test",
            },
        )
        self.assertIn(response.status_code, (400, 409))
        body = response.json()
        self.assertEqual(body["decision"], "denied")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertIn("protected", body["reason_code"])

    def test_proposal_only_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={
                "proposal": dict(SEED01_PROPOSAL),
                "user_input": "请退款订单 order_demo_001，金额 100.00",
                "source": "langgraph_example",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["decision"], "executed")
        self.assertEqual(body["adapter_call_count"], 1)
        self.assertFalse(body.get("scenario"))

    def test_neither_scenario_nor_proposal_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={"user_input": "hello", "source": "test"},
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["reason_code"], "missing_scenario_or_proposal")
        self.assertEqual(body["adapter_call_count"], 0)

    def test_proposal_only_protected_via_api(self) -> None:
        response = self.client.post(
            "/api/agent/propose",
            json={
                "proposal": {"intent": "refund", "principal_id": "forged"},
                "source": "test",
            },
        )
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["decision"], "denied")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertIn("protected", body["reason_code"])


if __name__ == "__main__":
    unittest.main()

