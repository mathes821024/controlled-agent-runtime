from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.models import PROTECTED_PROPOSAL_FIELDS
from controlled_agent_runtime.proposal_hook import (
    MODE_LOCAL_MODEL,
    MODE_OFF,
    ProposalHookError,
    local_model_available,
    resolve_proposal_hook_mode,
    run_proposal_hook,
    sanitize_hook_proposal,
)


class ProposalHookTests(unittest.TestCase):
    def test_default_mode_is_off(self) -> None:
        self.assertEqual(resolve_proposal_hook_mode({}), MODE_OFF)
        self.assertEqual(resolve_proposal_hook_mode({"CAR_PROPOSAL_HOOK": ""}), MODE_OFF)

    def test_local_model_aliases_normalize(self) -> None:
        self.assertEqual(
            resolve_proposal_hook_mode({"CAR_PROPOSAL_HOOK": "ollama"}),
            MODE_LOCAL_MODEL,
        )

    def test_unknown_mode_fails_closed(self) -> None:
        with self.assertRaises(ProposalHookError) as ctx:
            resolve_proposal_hook_mode({"CAR_PROPOSAL_HOOK": "openai"})
        self.assertIn("unknown_proposal_hook_mode", ctx.exception.reason_code)

    def test_local_model_never_available_and_never_downloads(self) -> None:
        self.assertFalse(local_model_available({"CAR_PROPOSAL_HOOK": "local_model"}))
        result = run_proposal_hook("refund order_demo_001", {"CAR_PROPOSAL_HOOK": "local_model"})
        self.assertFalse(result.ok)
        self.assertEqual(result.mode, MODE_LOCAL_MODEL)
        self.assertEqual(result.reason_code, "local_model_unavailable_no_download")
        self.assertFalse(result.download_attempted)
        self.assertIsNone(result.proposal)

    def test_default_hook_does_not_invent_a_proposal(self) -> None:
        result = run_proposal_hook("please refund", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.reason_code, "proposal_hook_disabled")
        self.assertIsNone(result.proposal)
        self.assertFalse(result.download_attempted)

    def test_sanitize_rejects_protected_fields(self) -> None:
        raw = {
            "intent": "refund",
            "appid": "app_demo_001",
            "term_id": "term_demo_001",
            "original_order_no": "order_demo_001",
            "original_transaction_date": "2026-09-01",
            "principal_id": "forged",
        }
        with self.assertRaises(ProposalHookError) as ctx:
            sanitize_hook_proposal(raw)
        self.assertIn("principal_id", ctx.exception.reason_code)
        self.assertTrue(PROTECTED_PROPOSAL_FIELDS)

    def test_sanitize_keeps_only_allowed_fields(self) -> None:
        raw = {
            "intent": "refund",
            "appid": "app_demo_001",
            "term_id": "term_demo_001",
            "original_order_no": "order_demo_001",
            "original_transaction_date": "2026-09-01",
            "requested_amount_minor": 10000,
            "merchant_email": "merchant-seed01@example.invalid",
        }
        cleaned = sanitize_hook_proposal(raw)
        self.assertEqual(cleaned["intent"], "refund")
        self.assertNotIn("principal_id", cleaned)
        self.assertNotIn("respCode", cleaned)


if __name__ == "__main__":
    unittest.main()
