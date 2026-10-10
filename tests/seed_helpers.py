from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_seed(name: str) -> dict:
    return json.loads((ROOT / "demo-seeds" / name).read_text(encoding="utf-8"))
