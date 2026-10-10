from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.models import RuntimeOutcome
from controlled_agent_runtime.runtime import ReferenceRuntime
from seed_helpers import load_seed


class Seed03RuntimeTests(unittest.TestCase):
    def test_seed_03_denied_full_refund_only_without_adapter(self) -> None:
        seed = load_seed("refund-seed-03.json")
        runtime = ReferenceRuntime()
        result = runtime.run_seed(seed)

        self.assertEqual(result.outcome, RuntimeOutcome.DENIED)
        self.assertEqual(result.reason_code, "full_refund_only")
        self.assertEqual(result.adapter_call_count, 0)
        self.assertEqual(result.event_names(), seed["expected"]["required_event_order"])
        for forbidden in seed["expected"]["forbidden_events"]:
            self.assertNotIn(forbidden, result.event_names())


if __name__ == "__main__":
    unittest.main()
