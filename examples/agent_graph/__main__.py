"""Run the stub graph against a live CAR demo.

Primary path (proposal-driven, no scenario)::

    PYTHONPATH=examples .venv/bin/python -m agent_graph \\
      --user-input "Please refund order_demo_001 for 100.00"

Canned demo / CI::

    PYTHONPATH=examples .venv/bin/python -m agent_graph --scenario safe_auto
"""

from __future__ import annotations

import argparse
import json
import os

DEFAULT_USER_INPUT = "Please refund order_demo_001 for 100.00"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Stub LangGraph example: draft a structured proposal from "
            "user_input (or a canned scenario) and POST it to "
            "CAR /api/agent/propose. CAR decides. No adapter tools."
        )
    )
    parser.add_argument(
        "--user-input",
        default=os.environ.get("CAR_USER_INPUT"),
        help="Natural-language request (primary agent path; no scenario required)",
    )
    parser.add_argument(
        "--scenario",
        default=os.environ.get("SCENARIO"),
        help="Optional demo/CI canned scenario (not required for the agent path)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CAR_BASE_URL", "http://127.0.0.1:8000"),
        help="CAR origin (default http://127.0.0.1:8000). VPS nginx: http://HOST/hitl",
    )
    parser.add_argument(
        "--client-trace-id",
        default=os.environ.get("CAR_CLIENT_TRACE_ID"),
        help="Optional client_trace_id forwarded to Ingress",
    )
    args = parser.parse_args()
    os.environ["CAR_BASE_URL"] = args.base_url

    try:
        from .graph import build_graph
    except ImportError as exc:
        raise SystemExit(
            "Agent extras missing. Run: .venv/bin/pip install -e '.[demo,agent]'"
        ) from exc

    user_input = (args.user_input or "").strip()
    scenario = (args.scenario or "").strip() or None
    if not user_input and not scenario:
        user_input = DEFAULT_USER_INPUT

    try:
        app = build_graph()
        result = app.invoke(
            {
                "user_input": user_input,
                "scenario": scenario,
                "client_trace_id": args.client_trace_id,
                "source": "langgraph_example",
            }
        )
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "decision": "denied",
                    "outcome": "failed_closed",
                    "reason_code": str(exc),
                    "adapter_call_count": 0,
                },
                indent=2,
            )
        )
        raise SystemExit(1) from exc

    body = result.get("car_response") or {}
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
    raise SystemExit(0)
