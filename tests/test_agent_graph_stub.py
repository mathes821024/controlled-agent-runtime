from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "agent_graph"
sys.path.insert(0, str(EXAMPLE_DIR))

from stub_llm import scenario_to_payload


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


class AgentGraphStubTests(unittest.TestCase):
    def test_safe_auto_payload_shape(self) -> None:
        payload = scenario_to_payload("safe_auto")
        self.assertEqual(payload["scenario"], "safe_auto")
        self.assertEqual(payload["source"], "langgraph_example")
        proposal = payload["proposal"]
        self.assertEqual(proposal["intent"], "refund")
        self.assertEqual(proposal["appid"], "app_demo_001")
        self.assertEqual(proposal["term_id"], "term_demo_001")
        self.assertEqual(proposal["original_order_no"], "order_demo_001")
        self.assertEqual(proposal["original_transaction_date"], "2026-09-01")
        self.assertEqual(proposal["requested_amount_minor"], 10000)
        self.assertTrue(str(proposal["merchant_email"]).endswith(".invalid"))
        self.assertNotIn("principal_id", proposal)
        self.assertNotIn("adapter_result", proposal)

    def test_four_scenarios_are_deterministic(self) -> None:
        expected_amounts = {
            "safe_auto": 10000,
            "human_review": 10001,
            "amount_mismatch": 8000,
        }
        for name, amount in expected_amounts.items():
            first = scenario_to_payload(name)
            second = scenario_to_payload(name)
            self.assertEqual(first, second)
            self.assertEqual(first["proposal"]["requested_amount_minor"], amount)
            self.assertNotIn("principal_id", first["proposal"])

        attack = scenario_to_payload("authority_attack")
        self.assertEqual(attack["scenario"], "authority_attack")
        self.assertEqual(attack["proposal"]["principal_id"], "forged")

    def test_client_trace_id_passthrough(self) -> None:
        payload = scenario_to_payload("safe_auto", client_trace_id="graph-1")
        self.assertEqual(payload["client_trace_id"], "graph-1")

    def test_unknown_scenario_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            scenario_to_payload("not_a_real_scenario")
        self.assertIn("unknown_scenario", str(ctx.exception))

    def test_this_module_does_not_import_langgraph(self) -> None:
        imported = _top_level_imports(Path(__file__).read_text(encoding="utf-8"))
        self.assertNotIn("langgraph", imported)
        self.assertNotIn("langchain", imported)
        self.assertNotIn("langchain_core", imported)

    def test_stub_module_does_not_import_langgraph_or_http(self) -> None:
        imported = _top_level_imports(
            (EXAMPLE_DIR / "stub_llm.py").read_text(encoding="utf-8")
        )
        self.assertNotIn("langgraph", imported)
        self.assertNotIn("langchain", imported)
        self.assertNotIn("httpx", imported)
        self.assertNotIn("openai", imported)

    def test_graph_source_only_posts_to_car_propose(self) -> None:
        graph = (EXAMPLE_DIR / "graph.py").read_text(encoding="utf-8")
        self.assertIn("/api/agent/propose", graph)
        self.assertIn("httpx.post", graph)
        self.assertNotIn("mock_refund", graph)
        self.assertNotIn("/refund", graph)
        self.assertNotIn("real_adapter", graph)


if __name__ == "__main__":
    unittest.main()
