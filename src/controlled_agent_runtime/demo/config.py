"""Demo process settings. Loopback by default. No secrets."""

from __future__ import annotations

import os
from typing import Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
UNSAFE_BIND_MESSAGE = (
    "Refusing to bind a non-loopback address. This HITL demo has no "
    "authentication. Bind 127.0.0.1 and use an SSH tunnel or a same-host "
    "reverse proxy, or pass --allow-public-bind if you accept the risk."
)


class UnsafeBindError(ValueError):
    """Raised when the demo would listen on a public interface without consent."""


def resolve_demo_host(
    explicit: Optional[str] = None,
    environ: Optional[dict[str, str]] = None,
) -> str:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    env = os.environ if environ is None else environ
    raw = str(env.get("CAR_DEMO_HOST", DEFAULT_HOST) or DEFAULT_HOST).strip()
    return raw or DEFAULT_HOST


def resolve_demo_port(
    explicit: Optional[int] = None,
    environ: Optional[dict[str, str]] = None,
) -> int:
    if explicit is not None:
        return int(explicit)
    env = os.environ if environ is None else environ
    raw = str(env.get("CAR_DEMO_PORT", DEFAULT_PORT) or DEFAULT_PORT).strip()
    port = int(raw)
    if port < 1 or port > 65535:
        raise ValueError("invalid_demo_port")
    return port


def assert_safe_bind(host: str, allow_public_bind: bool = False) -> str:
    normalized = (host or "").strip()
    if normalized in LOOPBACK_HOSTS:
        return normalized
    if allow_public_bind:
        return normalized
    raise UnsafeBindError(UNSAFE_BIND_MESSAGE)
