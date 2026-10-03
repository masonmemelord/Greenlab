"""Compatibility import. Use ``app.db`` in new code."""

from app.db import supabase

__all__ = ["supabase"]
