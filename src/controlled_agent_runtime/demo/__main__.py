"""python -m controlled_agent_runtime.demo"""

from __future__ import annotations

import argparse
import sys

from controlled_agent_runtime.demo.config import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    LOOPBACK_HOSTS,
    UnsafeBindError,
    assert_safe_bind,
    resolve_demo_host,
    resolve_demo_port,
)
from controlled_agent_runtime.proposal_hook import (
    ProposalHookError,
    resolve_proposal_hook_mode,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Human Acceptance UI + ReferenceRuntime (synthetic, no LLM)"
    )
    parser.add_argument("--host", default=None, help=f"Bind address (default {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=None, help=f"Bind port (default {DEFAULT_PORT})")
    parser.add_argument(
        "--allow-public-bind",
        action="store_true",
        help="Required to bind a non-loopback address. Demo has no auth.",
    )
    args = parser.parse_args()
    host = resolve_demo_host(args.host)
    port = resolve_demo_port(args.port)
    try:
        host = assert_safe_bind(host, allow_public_bind=args.allow_public_bind)
    except UnsafeBindError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Demo dependencies missing. Run: python3 -m venv .venv && "
            ".venv/bin/pip install -e '.[demo]'"
        ) from exc
    hook_mode = "off"
    try:
        hook_mode = resolve_proposal_hook_mode()
    except ProposalHookError as exc:
        hook_mode = exc.reason_code
    print("Human Acceptance UI:")
    print(f"http://{host}:{port}")
    print("Synthetic only. Real adapters disabled. No model download.")
    print(f"proposal_hook={hook_mode}")
    if host not in LOOPBACK_HOSTS:
        print(
            "WARNING: listening off loopback with no authentication. "
            "Prefer 127.0.0.1 plus an SSH tunnel or a same-host reverse proxy.",
            file=sys.stderr,
        )
    uvicorn.run(
        "controlled_agent_runtime.demo.app:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
