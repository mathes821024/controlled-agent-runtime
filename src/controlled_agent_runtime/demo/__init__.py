"""Local Human Acceptance demo: UI → API → ReferenceRuntime."""

__all__ = ["create_app"]

def create_app():
    from .app import create_app as _create
    return _create()
