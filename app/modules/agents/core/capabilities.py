"""capabilities.py — Capability matching helpers for Supervisor routing."""

from app.modules.agents.core.types import Capability


def match_capabilities(required: list[Capability], available: list[Capability]) -> bool:
    """Check if all required capabilities are satisfied by available capabilities."""
    req_set = set(required)
    avail_set = set(available)
    return req_set.issubset(avail_set)
