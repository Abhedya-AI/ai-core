"""exceptions.py — Standardized Agent Runtime Exceptions."""


class AgentRuntimeError(Exception):
    """Base exception for all agent runtime failures."""


class RetryableAgentException(AgentRuntimeError):
    """Transient exception eligible for automatic retry (e.g. LLM timeouts, network glitches)."""


class NonRetryableAgentException(AgentRuntimeError):
    """Deterministic exception NOT eligible for retry (e.g. validation, missing parameters, ontology errors)."""
