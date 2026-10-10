from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.models import RuntimeOutcome
from controlled_agent_runtime.runtime import ReferenceRuntime
from seed_helpers import load_seed


class Seed01RuntimeTests(unittest.TestCase):
    def test_seed_01_executes_once_with_ordered_evidence(self) -> None:
        seed = load_seed("refund-seed-01.json")
        runtime = ReferenceRuntime()
        result = runtime.run_seed(seed)

        self.assertEqual(result.outcome, RuntimeOutcome.EXECUTED)
        self.assertEqual(result.reason_code, "mock_business_success")
        self.assertEqual(result.adapter_call_count, 1)
        self.assertEqual(result.normalized_business_result, "REFUND_SUCCEEDED")
        self.assertEqual(result.resp_code, "00")
        self.assertEqual(result.event_names(), seed["expected"]["required_event_order"])
        for forbidden in seed["expected"]["forbidden_events"]:
            self.assertNotIn(forbidden, result.event_names())


if __name__ == "__main__":
    unittest.main()
