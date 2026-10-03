"""Compatibility entrypoint. New code should import ``app.main:app``."""

from app.main import app

__all__ = ["app"]
