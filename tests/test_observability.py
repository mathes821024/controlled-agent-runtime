from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.observability import start_trace

LANGFUSE_ENV = (
    "CAR_LANGFUSE_PUBLIC_KEY",
    "CAR_LANGFUSE_SECRET_KEY",
    "CAR_LANGFUSE_HOST",
)


class ObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = {
            key: os.environ.get(key)
            for key in (*LANGFUSE_ENV, "CAR_TRACE_JSONL")
        }
        for key in LANGFUSE_ENV:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

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

    def test_partial_langfuse_env_does_not_raise(self) -> None:
        os.environ["CAR_LANGFUSE_PUBLIC_KEY"] = "pk-test"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            sys.modules.pop("langfuse", None)
            car_id = start_trace("graph.run", jsonl_path=path).end()
            self.assertTrue(car_id)
            self.assertNotIn("langfuse", sys.modules)


if __name__ == "__main__":
    unittest.main()
