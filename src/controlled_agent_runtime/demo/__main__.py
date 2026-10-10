"""python -m controlled_agent_runtime.demo"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Human Acceptance UI + ReferenceRuntime")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Demo dependencies missing. Run: python3 -m venv .venv && "
            ".venv/bin/pip install -e '.[demo]'"
        ) from exc
    print("Human Acceptance UI:")
    print(f"http://{args.host}:{args.port}")
    print("Synthetic only. Real adapters disabled. Local only.")
    uvicorn.run(
        "controlled_agent_runtime.demo.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
