from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "agent_graph"
sys.path.insert(0, str(EXAMPLE_DIR))

from chat_llm import (
    ChatCompatibleAgentLlm,
    ProposalDraft,
    resolve_chat_config,
    structured_to_proposal,
)
from llm import StubAgentLlm, get_agent_llm, resolve_agent_llm_mode
from stub_llm import (
    ALLOWED_HOOK_FIELDS,
    scenario_to_payload,
    user_input_to_payload,
    user_input_to_proposal,
)


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

    def test_english_user_input_to_proposal_without_scenario(self) -> None:
        payload = user_input_to_payload("Please refund order_demo_001 for 100.00")
        self.assertNotIn("scenario", payload)
        self.assertEqual(payload["user_input"], "Please refund order_demo_001 for 100.00")
        proposal = payload["proposal"]
        self.assertEqual(proposal["original_order_no"], "order_demo_001")
        self.assertEqual(proposal["requested_amount_minor"], 10000)
        self.assertTrue(set(proposal) <= ALLOWED_HOOK_FIELDS)

    def test_chinese_user_input_to_proposal_without_scenario(self) -> None:
        payload = user_input_to_payload("帮我退一下订单 order_demo_001，金额 100 元。")
        self.assertNotIn("scenario", payload)
        self.assertEqual(payload["proposal"]["requested_amount_minor"], 10000)
        self.assertEqual(
            payload["proposal"]["merchant_email"],
            "merchant-seed01@example.invalid",
        )

    def test_user_input_maps_review_and_mismatch_phrases(self) -> None:
        review = user_input_to_proposal("Please refund order_demo_002 for 100.01")
        self.assertEqual(review["requested_amount_minor"], 10001)
        mismatch = user_input_to_proposal("请退款 order_demo_003，金额 80.00")
        self.assertEqual(mismatch["requested_amount_minor"], 8000)

    def test_default_llm_mode_is_stub(self) -> None:
        previous = os.environ.get("CAR_AGENT_LLM")
        os.environ.pop("CAR_AGENT_LLM", None)
        try:
            self.assertEqual(resolve_agent_llm_mode({}), "stub")
            self.assertIsInstance(get_agent_llm({}), StubAgentLlm)
        finally:
            if previous is None:
                os.environ.pop("CAR_AGENT_LLM", None)
            else:
                os.environ["CAR_AGENT_LLM"] = previous

    def test_local_and_openai_modes_use_chat_provider(self) -> None:
        for mode in ("local", "openai"):
            provider = get_agent_llm({"CAR_AGENT_LLM": mode})
            self.assertIsInstance(provider, ChatCompatibleAgentLlm)
            self.assertEqual(provider.name, mode)

    def test_local_mode_requires_model(self) -> None:
        provider = ChatCompatibleAgentLlm("local", {})
        with self.assertRaises(ValueError) as ctx:
            provider.draft_proposal("Please refund order_demo_001 for 100.00")
        self.assertIn("missing_agent_llm_model", str(ctx.exception))

    def test_openai_mode_requires_api_key(self) -> None:
        provider = ChatCompatibleAgentLlm(
            "openai", {"CAR_AGENT_LLM_MODEL": "demo-model"}
        )
        with self.assertRaises(ValueError) as ctx:
            provider.draft_proposal("Please refund order_demo_001 for 100.00")
        self.assertIn("missing_agent_llm_api_key", str(ctx.exception))

    def test_local_defaults_loopback_openai_compatible_url(self) -> None:
        config = resolve_chat_config("local", {"CAR_AGENT_LLM_MODEL": "demo-local"})
        self.assertEqual(config["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(config["model"], "demo-local")

    def test_structured_output_schema_is_allowed_fields_only(self) -> None:
        self.assertEqual(set(ProposalDraft.model_fields), set(ALLOWED_HOOK_FIELDS))

    def test_structured_to_proposal_drops_protected_and_extras(self) -> None:
        class FakeDraft:
            def model_dump(self) -> dict:
                return {
                    "intent": "refund",
                    "appid": "app_demo_001",
                    "term_id": "term_demo_001",
                    "original_order_no": "order_demo_001",
                    "original_transaction_date": "2026-09-01",
                    "requested_amount_minor": 10000,
                    "merchant_email": "merchant-seed01@example.invalid",
                    "principal_id": "forged",
                    "adapter_result": "nope",
                }

        proposal = structured_to_proposal(FakeDraft())
        self.assertEqual(proposal["intent"], "refund")
        self.assertEqual(proposal["requested_amount_minor"], 10000)
        self.assertNotIn("principal_id", proposal)
        self.assertNotIn("adapter_result", proposal)
        self.assertTrue(set(proposal) <= ALLOWED_HOOK_FIELDS)

    def test_chat_provider_uses_langchain_structured_output(self) -> None:
        from unittest.mock import MagicMock, patch

        draft = ProposalDraft(
            intent="refund",
            appid="app_demo_001",
            term_id="term_demo_001",
            original_order_no="order_demo_001",
            original_transaction_date="2026-09-01",
            requested_amount_minor=10000,
            merchant_email="merchant-seed01@example.invalid",
        )
        with patch("chat_llm.invoke_structured_proposal", return_value=draft) as mocked:
            provider = ChatCompatibleAgentLlm(
                "local", {"CAR_AGENT_LLM_MODEL": "demo-local"}
            )
            proposal = provider.draft_proposal(
                "帮我退一下订单 order_demo_001，金额 100 元。"
            )
        mocked.assert_called_once()
        self.assertEqual(proposal["original_order_no"], "order_demo_001")
        self.assertNotIn("scenario", proposal)
        self.assertTrue(set(proposal) <= ALLOWED_HOOK_FIELDS)

    def test_chat_provider_fail_closed_without_fallback(self) -> None:
        from unittest.mock import patch

        with patch(
            "chat_llm.invoke_structured_proposal",
            side_effect=ConnectionError("refused"),
        ):
            provider = ChatCompatibleAgentLlm(
                "local", {"CAR_AGENT_LLM_MODEL": "demo-local"}
            )
            with self.assertRaises(ValueError) as ctx:
                provider.draft_proposal("Please refund order_demo_001 for 100.00")
        self.assertIn("agent_llm_unavailable", str(ctx.exception))

    def test_chat_provider_optional_stub_fallback(self) -> None:
        from unittest.mock import patch

        with patch(
            "chat_llm.invoke_structured_proposal",
            side_effect=ConnectionError("refused"),
        ):
            provider = ChatCompatibleAgentLlm(
                "local",
                {
                    "CAR_AGENT_LLM_MODEL": "demo-local",
                    "CAR_AGENT_LLM_FALLBACK": "stub",
                },
            )
            proposal = provider.draft_proposal(
                "Please refund order_demo_001 for 100.00"
            )
        self.assertEqual(proposal["requested_amount_minor"], 10000)

    def test_unknown_llm_mode_fail_closed(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            resolve_agent_llm_mode({"CAR_AGENT_LLM": "ollama"})
        self.assertIn("unknown_agent_llm", str(ctx.exception))

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

    def test_llm_module_does_not_import_langgraph_or_http(self) -> None:
        imported = _top_level_imports((EXAMPLE_DIR / "llm.py").read_text(encoding="utf-8"))
        self.assertNotIn("langgraph", imported)
        self.assertNotIn("httpx", imported)
        self.assertNotIn("langchain_openai", imported)
        self.assertNotIn("openai", imported)

    def test_chat_llm_source_uses_langchain_structured_output(self) -> None:
        source = (EXAMPLE_DIR / "chat_llm.py").read_text(encoding="utf-8")
        self.assertIn("from langchain_openai import ChatOpenAI", source)
        self.assertIn("with_structured_output", source)
        self.assertIn("def invoke_structured_proposal", source)
        self.assertIn("ProposalDraft", source)
        self.assertNotIn("mock_refund", source)
        self.assertNotIn("/refund", source)

    def test_chat_llm_module_does_not_import_langgraph_or_httpx(self) -> None:
        imported = _top_level_imports(
            (EXAMPLE_DIR / "chat_llm.py").read_text(encoding="utf-8")
        )
        self.assertNotIn("langgraph", imported)
        self.assertNotIn("httpx", imported)

    def test_graph_source_only_posts_to_car_propose(self) -> None:
        graph = (EXAMPLE_DIR / "graph.py").read_text(encoding="utf-8")
        self.assertIn("/api/agent/propose", graph)
        self.assertIn("httpx.post", graph)
        self.assertNotIn("mock_refund", graph)
        self.assertNotIn("/refund", graph)
        self.assertNotIn("real_adapter", graph)
        self.assertNotIn("bind_tools", graph)
        self.assertNotIn("ToolNode", graph)
        self.assertNotIn("@tool", graph)

    def test_graph_state_and_nodes(self) -> None:
        graph = (EXAMPLE_DIR / "graph.py").read_text(encoding="utf-8")
        for field in (
            "user_input",
            "proposal",
            "car_response",
            "decision",
            "trace_id",
        ):
            self.assertIn(field, graph)
        for node in ("understand", "draft_proposal", "submit_to_car", "done"):
            self.assertIn(f'"{node}"', graph)


if __name__ == "__main__":
    unittest.main()
