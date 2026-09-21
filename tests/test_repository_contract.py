from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.validation import PROTECTED_FIELDS, validate_repository


class RepositoryContractTests(unittest.TestCase):
    def test_repository_validation_passes(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_policy_protects_privileged_fields(self) -> None:
        policy = json.loads(
            (ROOT / "policy/examples/refund-demo-policy.json").read_text(encoding="utf-8")
        )
        forbidden = set(policy["proposal"]["forbidden_fields"])
        self.assertTrue(PROTECTED_FIELDS <= forbidden)

    def test_seed_uses_only_mock_execution(self) -> None:
        seed = json.loads(
            (ROOT / "demo-seeds/refund-seed-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(seed["data_mode"], "synthetic_only")
        self.assertEqual(seed["expected"]["adapter_call_count"], 1)
        self.assertIn("mock_adapter_called", seed["expected"]["required_event_order"])
        self.assertIn("real_adapter_called", seed["expected"]["forbidden_events"])


if __name__ == "__main__":
    unittest.main()
