"""Internal observability tracer.

JSONL is the guaranteed sink. Langfuse is optional and never imported unless
``CAR_LANGFUSE_PUBLIC_KEY``, ``CAR_LANGFUSE_SECRET_KEY``, and
``CAR_LANGFUSE_HOST`` are all set. Incomplete env or a failed import stays
JSONL-only and does not raise.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

ENV_TRACE_JSONL = "CAR_TRACE_JSONL"
ENV_LANGFUSE_PUBLIC_KEY = "CAR_LANGFUSE_PUBLIC_KEY"
ENV_LANGFUSE_SECRET_KEY = "CAR_LANGFUSE_SECRET_KEY"
ENV_LANGFUSE_HOST = "CAR_LANGFUSE_HOST"
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


def _langfuse_config(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str] | None:
    env = os.environ if environ is None else environ
    public_key = str(env.get(ENV_LANGFUSE_PUBLIC_KEY, "") or "").strip()
    secret_key = str(env.get(ENV_LANGFUSE_SECRET_KEY, "") or "").strip()
    host = str(env.get(ENV_LANGFUSE_HOST, "") or "").strip()
    if not public_key or not secret_key or not host:
        return None
    return {
        "public_key": public_key,
        "secret_key": secret_key,
        "host": host,
    }


def _try_langfuse_client(
    environ: Mapping[str, str] | None = None,
) -> Any | None:
    """Import Langfuse only when env is complete. Never raise."""
    config = _langfuse_config(environ)
    if config is None:
        return None
    try:
        from langfuse import Langfuse
    except Exception:
        return None
    try:
        return Langfuse(
            public_key=config["public_key"],
            secret_key=config["secret_key"],
            host=config["host"],
        )
    except Exception:
        return None


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
        payload = dict(fields)
        try:
            if event == "start" and hasattr(client, "trace"):
                client.trace(
                    id=self.car_trace_id,
                    name=name,
                    metadata=payload,
                )
            elif event == "span" and hasattr(client, "span"):
                client.span(
                    trace_id=self.car_trace_id,
                    name=name,
                    metadata=payload,
                )
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
