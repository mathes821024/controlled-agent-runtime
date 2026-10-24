"""Controlled Agent Runtime.

Gate 0: frozen contracts + static validation.
Gate 1 Slice 1: minimal in-memory reference runtime (synthetic only).
Gate 1 Slice 2: Human Acceptance UI over the reference runtime.
"""

__version__ = "0.1.0-g1-slice2"

from .runtime import ReferenceRuntime

__all__ = ["ReferenceRuntime", "__version__"]
