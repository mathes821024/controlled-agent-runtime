from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlled_agent_runtime.demo.config import (
    UnsafeBindError,
    assert_safe_bind,
    resolve_demo_host,
    resolve_demo_port,
)


class DemoBindTests(unittest.TestCase):
    def test_default_host_is_loopback(self) -> None:
        self.assertEqual(resolve_demo_host(environ={}), "127.0.0.1")
        self.assertEqual(resolve_demo_port(environ={}), 8000)

    def test_loopback_is_allowed(self) -> None:
        self.assertEqual(assert_safe_bind("127.0.0.1"), "127.0.0.1")
        self.assertEqual(assert_safe_bind("localhost"), "localhost")
        self.assertEqual(assert_safe_bind("::1"), "::1")

    def test_public_bind_fails_closed_without_consent(self) -> None:
        with self.assertRaises(UnsafeBindError):
            assert_safe_bind("0.0.0.0")
        with self.assertRaises(UnsafeBindError):
            assert_safe_bind("0.0.0.0", allow_public_bind=False)

    def test_public_bind_requires_explicit_flag(self) -> None:
        self.assertEqual(assert_safe_bind("0.0.0.0", allow_public_bind=True), "0.0.0.0")

    def test_env_overrides(self) -> None:
        self.assertEqual(
            resolve_demo_host(environ={"CAR_DEMO_HOST": "localhost"}),
            "localhost",
        )
        self.assertEqual(resolve_demo_port(environ={"CAR_DEMO_PORT": "9001"}), 9001)


if __name__ == "__main__":
    unittest.main()
