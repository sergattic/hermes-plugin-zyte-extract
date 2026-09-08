"""Zyte Extract API plugin — see provider.py for rationale."""

from __future__ import annotations

from .provider import ZyteExtractProvider


def register(ctx) -> None:  # noqa: ARG001 — ctx unused, single provider registration
    ctx.register_web_search_provider(ZyteExtractProvider())
