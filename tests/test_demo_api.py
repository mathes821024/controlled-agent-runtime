from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None  # type: ignore

from controlled_agent_runtime.demo.app import create_app


@unittest.skipIf(TestClient is None, "fastapi demo extras not installed")
class DemoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def test_health(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["real_adapters"], "disabled")

    def test_safe_auto_executed(self) -> None:
        response = self.client.post("/api/demo/run", json={"scenario": "safe_auto"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "executed")
        self.assertEqual(body["adapter_call_count"], 1)
        self.assertEqual(body["reason_code"], "mock_business_success")
        self.assertEqual(body["ui"]["source"], "ReferenceRuntime")
        names = [item["name"] for item in body["evidence"]]
        self.assertIn("mock_adapter_called", names)
        self.assertEqual(names[-1], "trace_completed")

    def test_human_review_no_adapter(self) -> None:
        response = self.client.post("/api/demo/run", json={"scenario": "human_review"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "needs_review")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertEqual(body["reason_code"], "demo_amount_threshold")
        names = [item["name"] for item in body["evidence"]]
        self.assertNotIn("mock_adapter_called", names)

    def test_amount_mismatch_denied(self) -> None:
        response = self.client.post("/api/demo/run", json={"scenario": "amount_mismatch"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "denied")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertEqual(body["reason_code"], "full_refund_only")

    def test_authority_attack_failed_closed(self) -> None:
        response = self.client.post("/api/demo/run", json={"scenario": "authority_attack"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "failed_closed")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertIn("principal_id", body["reason_code"])
        names = [item["name"] for item in body["evidence"]]
        self.assertNotIn("mock_adapter_called", names)
        self.assertNotIn("trusted_context_bound", names)

    def test_unknown_scenario_fail_closed(self) -> None:
        response = self.client.post("/api/demo/run", json={"scenario": "not_a_real_scenario"})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        detail = body.get("detail", body)
        self.assertEqual(detail["outcome"], "failed_closed")
        self.assertEqual(detail["reason_code"], "unknown_scenario")
        self.assertEqual(detail["adapter_call_count"], 0)

    def test_ui_index_served(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("受控执行控制台", response.text)
        self.assertIn("/api/demo/run", response.text)



    def test_runtime_exception_no_fake_success(self) -> None:
        from unittest.mock import patch

        with patch(
            "controlled_agent_runtime.demo.app.ReferenceRuntime.run_seed",
            side_effect=RuntimeError("boom"),
        ):
            response = self.client.post("/api/demo/run", json={"scenario": "safe_auto"})
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["outcome"], "failed_closed")
        self.assertEqual(body["adapter_call_count"], 0)
        self.assertNotEqual(body["outcome"], "executed")
        self.assertEqual(body["ui"]["source"], "error")

if __name__ == "__main__":
    unittest.main()
