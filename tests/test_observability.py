from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.observability import (
    resolve_langfuse_config,
    start_trace,
)

LANGFUSE_ENV = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "CAR_LANGFUSE_PUBLIC_KEY",
    "CAR_LANGFUSE_SECRET_KEY",
    "CAR_LANGFUSE_HOST",
    "CAR_LANGFUSE_BASE_URL",
    "CAR_TRACE_JSONL",
)
OBSERVABILITY_SOURCE = (
    ROOT / "src" / "controlled_agent_runtime" / "observability.py"
).read_text(encoding="utf-8")


class ObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = {key: os.environ.get(key) for key in LANGFUSE_ENV}
        self._langfuse_module = sys.modules.get("langfuse")
        for key in LANGFUSE_ENV:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if self._langfuse_module is None:
            sys.modules.pop("langfuse", None)
        else:
            sys.modules["langfuse"] = self._langfuse_module

    def test_jsonl_records_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            handle = start_trace(
                "graph.run",
                client_trace_id="client-1",
                metadata={"source": "test"},
                jsonl_path=path,
            )
            handle.span("car.propose", decision="pending")
            car_id = handle.end(decision="executed")
            self.assertTrue(car_id)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 2)
            first = json.loads(lines[0])
            self.assertEqual(first["client_trace_id"], "client-1")
            self.assertEqual(first["car_trace_id"], car_id)

    def test_jsonl_records_include_event_and_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            handle = start_trace("graph.run", client_trace_id="client-1", jsonl_path=path)
            handle.span("car.propose", decision="pending")
            handle.end(decision="executed")
            records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([row["event"] for row in records], ["start", "span", "end"])
            self.assertEqual(records[0]["name"], "graph.run")
            self.assertEqual(records[1]["name"], "car.propose")
            self.assertEqual(records[1]["decision"], "pending")

    def test_car_trace_jsonl_env_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "from-env.jsonl"
            os.environ["CAR_TRACE_JSONL"] = str(path)
            handle = start_trace("graph.run", client_trace_id="client-env")
            car_id = handle.end()
            self.assertTrue(path.is_file())
            first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(first["car_trace_id"], car_id)
            self.assertEqual(first["client_trace_id"], "client-env")

    def test_incomplete_langfuse_env_never_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            sys.modules.pop("langfuse", None)
            start_trace("graph.run", jsonl_path=path).end()
            self.assertNotIn("langfuse", sys.modules)

    def test_incomplete_official_langfuse_env_never_imports(self) -> None:
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-test"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            sys.modules.pop("langfuse", None)
            car_id = start_trace("graph.run", jsonl_path=path).end()
            self.assertTrue(car_id)
            self.assertNotIn("langfuse", sys.modules)

    def test_partial_langfuse_env_does_not_raise(self) -> None:
        os.environ["CAR_LANGFUSE_PUBLIC_KEY"] = "pk-test"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            sys.modules.pop("langfuse", None)
            car_id = start_trace("graph.run", jsonl_path=path).end()
            self.assertTrue(car_id)
            self.assertNotIn("langfuse", sys.modules)

    def test_official_env_names_win_over_car_aliases(self) -> None:
        config = resolve_langfuse_config(
            {
                "LANGFUSE_PUBLIC_KEY": "official-pk",
                "LANGFUSE_SECRET_KEY": "official-sk",
                "LANGFUSE_BASE_URL": "http://official.example.invalid",
                "CAR_LANGFUSE_PUBLIC_KEY": "car-pk",
                "CAR_LANGFUSE_SECRET_KEY": "car-sk",
                "CAR_LANGFUSE_HOST": "http://car.example.invalid",
            }
        )
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config["public_key"], "official-pk")
        self.assertEqual(config["secret_key"], "official-sk")
        self.assertEqual(config["base_url"], "http://official.example.invalid")

    def test_car_aliases_map_host_to_base_url(self) -> None:
        config = resolve_langfuse_config(
            {
                "CAR_LANGFUSE_PUBLIC_KEY": "pk-test",
                "CAR_LANGFUSE_SECRET_KEY": "sk-test",
                "CAR_LANGFUSE_HOST": "http://langfuse.example.invalid",
            }
        )
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config["public_key"], "pk-test")
        self.assertEqual(config["base_url"], "http://langfuse.example.invalid")

    def test_source_uses_current_get_client_api_not_legacy(self) -> None:
        self.assertIn("from langfuse import get_client", OBSERVABILITY_SOURCE)
        self.assertIn("start_as_current_observation", OBSERVABILITY_SOURCE)
        self.assertNotIn("from langfuse import Langfuse", OBSERVABILITY_SOURCE)
        self.assertNotIn("Langfuse(", OBSERVABILITY_SOURCE)
        self.assertNotIn("client.trace(", OBSERVABILITY_SOURCE)
        self.assertNotIn("client.span(", OBSERVABILITY_SOURCE)

    def test_complete_env_uses_get_client_observation_and_flush(self) -> None:
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-test"
        os.environ["LANGFUSE_BASE_URL"] = "http://langfuse.example.invalid"
        calls: list[tuple[Any, ...]] = []

        class FakeObservation:
            def __enter__(self) -> FakeObservation:
                return self

            def __exit__(self, *args: object) -> bool:
                return False

            def update(self, **kwargs: Any) -> None:
                calls.append(("update", kwargs))

        class FakeClient:
            def start_as_current_observation(self, **kwargs: Any) -> FakeObservation:
                calls.append(("start", kwargs))
                return FakeObservation()

            def flush(self) -> None:
                calls.append(("flush",))

        fake = types.ModuleType("langfuse")
        fake.get_client = lambda: FakeClient()  # type: ignore[attr-defined]
        sys.modules["langfuse"] = fake

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            handle = start_trace("graph.run", jsonl_path=path)
            handle.span("car.propose", decision="pending")
            handle.end(decision="executed")
            self.assertTrue(path.is_file())

        start_calls = [item for item in calls if item[0] == "start"]
        self.assertGreaterEqual(len(start_calls), 1)
        self.assertEqual(start_calls[0][1].get("as_type"), "span")
        self.assertIn(("flush",), calls)

    def test_langfuse_exception_stays_jsonl_only(self) -> None:
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-test"
        os.environ["LANGFUSE_BASE_URL"] = "http://langfuse.example.invalid"
        fake = types.ModuleType("langfuse")

        def _boom() -> None:
            raise RuntimeError("langfuse unavailable")

        fake.get_client = _boom  # type: ignore[attr-defined]
        sys.modules["langfuse"] = fake
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            car_id = start_trace("graph.run", jsonl_path=path).end()
            self.assertTrue(car_id)
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
