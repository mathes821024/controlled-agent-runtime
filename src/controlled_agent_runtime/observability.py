"""Internal observability tracer.

JSONL is the guaranteed sink. Langfuse is optional and is never imported
unless a complete credential set is present.

Official env names (preferred, used when calling the current SDK):

- ``LANGFUSE_PUBLIC_KEY``
- ``LANGFUSE_SECRET_KEY``
- ``LANGFUSE_BASE_URL``

CAR aliases (mapped onto the official names when official values are empty):

- ``CAR_LANGFUSE_PUBLIC_KEY``
- ``CAR_LANGFUSE_SECRET_KEY``
- ``CAR_LANGFUSE_BASE_URL`` or legacy ``CAR_LANGFUSE_HOST``

When env is complete the current Langfuse API is used
(``from langfuse import get_client`` then
``get_client().start_as_current_observation(as_type="span", name=...)`` as a
context manager, and ``flush()`` on end). Target the current major that
exposes ``get_client`` (Langfuse Python v3+ / v4 OpenTelemetry). ``langfuse``
is not a ``.[demo]`` dependency.

Incomplete env, a missing package, or any Langfuse exception stays JSONL-only
and never raises into CAR. Langfuse is an observability sink only — never
Policy, Approval, or Execution.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

ENV_TRACE_JSONL = "CAR_TRACE_JSONL"
ENV_LANGFUSE_PUBLIC_KEY = "LANGFUSE_PUBLIC_KEY"
ENV_LANGFUSE_SECRET_KEY = "LANGFUSE_SECRET_KEY"
ENV_LANGFUSE_BASE_URL = "LANGFUSE_BASE_URL"
ENV_CAR_LANGFUSE_PUBLIC_KEY = "CAR_LANGFUSE_PUBLIC_KEY"
ENV_CAR_LANGFUSE_SECRET_KEY = "CAR_LANGFUSE_SECRET_KEY"
ENV_CAR_LANGFUSE_BASE_URL = "CAR_LANGFUSE_BASE_URL"
ENV_CAR_LANGFUSE_HOST = "CAR_LANGFUSE_HOST"
DEFAULT_JSONL_RELATIVE = Path("var/car-traces.jsonl")


def resolve_jsonl_path(jsonl_path: str | Path | None = None) -> Path:
    """Return the JSONL sink path.

    Precedence: explicit ``jsonl_path`` override, then ``CAR_TRACE_JSONL``,
    then ``var/car-traces.jsonl`` under the current working directory.
    """
    if jsonl_path is not None:
        return Path(jsonl_path)
    raw = str(os.environ.get(ENV_TRACE_JSONL, "") or "").strip()
    if raw:
        return Path(raw)
    return Path.cwd() / DEFAULT_JSONL_RELATIVE


def _first_nonempty(env: Mapping[str, str], *keys: str) -> str:
    for key in keys:
        value = str(env.get(key, "") or "").strip()
        if value:
            return value
    return ""


def resolve_langfuse_config(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str] | None:
    """Return official Langfuse credentials, or None when incomplete.

    Official names win when both official and ``CAR_LANGFUSE_*`` are set.
    """
    env = os.environ if environ is None else environ
    public_key = _first_nonempty(
        env, ENV_LANGFUSE_PUBLIC_KEY, ENV_CAR_LANGFUSE_PUBLIC_KEY
    )
    secret_key = _first_nonempty(
        env, ENV_LANGFUSE_SECRET_KEY, ENV_CAR_LANGFUSE_SECRET_KEY
    )
    base_url = _first_nonempty(
        env,
        ENV_LANGFUSE_BASE_URL,
        ENV_CAR_LANGFUSE_BASE_URL,
        ENV_CAR_LANGFUSE_HOST,
    )
    if not public_key or not secret_key or not base_url:
        return None
    return {
        "public_key": public_key,
        "secret_key": secret_key,
        "base_url": base_url,
    }


def _apply_official_langfuse_env(config: Mapping[str, str]) -> None:
    """Expose credentials under official names so ``get_client()`` can read them."""
    mapping = {
        ENV_LANGFUSE_PUBLIC_KEY: config["public_key"],
        ENV_LANGFUSE_SECRET_KEY: config["secret_key"],
        ENV_LANGFUSE_BASE_URL: config["base_url"],
    }
    for key, value in mapping.items():
        if not str(os.environ.get(key, "") or "").strip():
            os.environ[key] = value


def _try_langfuse_client(
    environ: Mapping[str, str] | None = None,
) -> Any | None:
    """Import current Langfuse only when env is complete. Never raise."""
    config = resolve_langfuse_config(environ)
    if config is None:
        return None
    try:
        _apply_official_langfuse_env(config)
        from langfuse import get_client
    except Exception:
        return None
    try:
        client = get_client()
    except Exception:
        return None
    if client is None:
        return None
    return client


class TraceHandle:
    """In-process handle for one ``car_trace_id`` parent trace."""

    def __init__(
        self,
        *,
        name: str,
        car_trace_id: str,
        client_trace_id: str | None,
        jsonl_path: Path,
        langfuse: Any | None = None,
    ) -> None:
        self._name = name
        self.car_trace_id = car_trace_id
        self.client_trace_id = client_trace_id
        self._jsonl_path = jsonl_path
        self._langfuse = langfuse

    def span(self, name: str, **fields: Any) -> None:
        self._record("span", name, **fields)

    def end(self, **fields: Any) -> str:
        self._record("end", self._name, **fields)
        self._flush_langfuse()
        return self.car_trace_id

    def _record(self, event: str, name: str, **fields: Any) -> None:
        record: dict[str, Any] = {
            "event": event,
            "name": name,
            "car_trace_id": self.car_trace_id,
            "client_trace_id": self.client_trace_id,
        }
        reserved = set(record)
        for key, value in fields.items():
            if key in reserved:
                continue
            record[key] = value
        path = self._jsonl_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self._emit_langfuse(event, name, fields)

    def _emit_langfuse(self, event: str, name: str, fields: Mapping[str, Any]) -> None:
        client = self._langfuse
        if client is None:
            return
        try:
            start = getattr(client, "start_as_current_observation", None)
            if not callable(start):
                return
            with start(as_type="span", name=name) as observation:
                update = getattr(observation, "update", None)
                if callable(update):
                    payload = {
                        "event": event,
                        "car_trace_id": self.car_trace_id,
                        "client_trace_id": self.client_trace_id,
                        **dict(fields),
                    }
                    update(metadata=payload)
        except Exception:
            return

    def _flush_langfuse(self) -> None:
        client = self._langfuse
        if client is None:
            return
        flush = getattr(client, "flush", None)
        if not callable(flush):
            return
        try:
            flush()
        except Exception:
            return


def start_trace(
    name: str,
    *,
    client_trace_id: str | None = None,
    metadata: dict | None = None,
    jsonl_path: str | Path | None = None,
) -> TraceHandle:
    """Open a parent trace and append a JSONL start record.

    ``jsonl_path`` is a test/injection override. Production callers rely on
    ``CAR_TRACE_JSONL`` or the default ``var/car-traces.jsonl`` path.
    """
    handle = TraceHandle(
        name=name,
        car_trace_id=str(uuid.uuid4()),
        client_trace_id=client_trace_id,
        jsonl_path=resolve_jsonl_path(jsonl_path),
        langfuse=_try_langfuse_client(),
    )
    start_fields: dict[str, Any] = {}
    if metadata:
        start_fields["metadata"] = metadata
    handle._record("start", name, **start_fields)
    return handle
