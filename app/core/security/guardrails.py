"""
app/core/security/guardrails.py — Prompt Injection & Input Security Guardrails.

Scans incoming user queries, prompts, and incident descriptions for adversarial
prompt injection attacks, jailbreak attempts, and system override instructions
before they reach LLM/Agent reasoning pipelines.

Threat Vectors Mitigated:
  1. System Prompt Overrides ("Ignore previous instructions", "You are now DAN")
  2. Rule Bypasses ("Disregard safety rules", "Pretend compliance does not apply")
  3. Context Leakage ("Output system prompt", "Print initial instructions")
  4. Delimiter Hijacking ("```system", "</user_input>")
"""

from __future__ import annotations

import re
from typing import Any

from app.api.exceptions import AbhedyaException
from app.core.logging import get_logger

log = get_logger("security.guardrails")


class PromptInjectionError(AbhedyaException):
    """Raised when an adversarial prompt injection attack is detected."""
    code = "PROMPT_INJECTION_DETECTED"
    message = "Prompt injection attempt detected."
    status = 400

    def __init__(self, pattern_matched: str, message: str = "Prompt injection attempt detected.") -> None:
        super().__init__(
            message=message,
            code="PROMPT_INJECTION_DETECTED",
            details={"pattern": pattern_matched},
        )



# ── Adversarial Patterns ──────────────────────────────────────────────────────

INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # System prompt override
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I), "IGNORE_INSTRUCTIONS"),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+rules?", re.I), "DISREGARD_RULES"),
    (re.compile(r"forget\s+(everything|all\s+previous)", re.I), "FORGET_CONTEXT"),
    # Persona / Jailbreak modes
    (re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|jailbreak|developer|god)\s+mode", re.I), "JAILBREAK_MODE"),
    (re.compile(r"act\s+as\s+an?\s+unfiltered", re.I), "ACT_UNFILTERED"),
    (re.compile(r"pretend\s+(safety|compliance|rules)\s+do(es)?\s+not\s+exist", re.I), "BYPASS_SAFETY"),
    # System prompt extraction
    (re.compile(r"(output|print|show|reveal|repeat)\s+(the\s+)?(system|initial)\s+prompt", re.I), "PROMPT_LEAK"),
    (re.compile(r"what\s+are\s+your\s+(original|system)\s+instructions\?", re.I), "PROMPT_LEAK_QUESTION"),
    # Roleplay override
    (re.compile(r"\[system\]", re.I), "SYSTEM_TAG_HIJACK"),
    (re.compile(r"</?system>", re.I), "SYSTEM_XML_HIJACK"),
    (re.compile(r"sudo\s+mode", re.I), "SUDO_MODE"),
]


class PromptGuardrailScanner:
    """Scanner for detecting adversarial prompt injection in inputs."""

    @classmethod
    def scan(cls, input_text: str | None, raise_on_detection: bool = True) -> tuple[bool, str | None]:
        """
        Scan text for prompt injection patterns.

        Args:
            input_text: User provided query or payload string.
            raise_on_detection: If True, raises PromptInjectionError on match.

        Returns:
            Tuple of (is_clean, matched_pattern_label).
        """
        if not input_text:
            return True, None

        for pattern, label in INJECTION_PATTERNS:
            if pattern.search(input_text):
                log.warning(f"SECURITY ALERT: Prompt injection attempt detected! Label: {label}")
                if raise_on_detection:
                    raise PromptInjectionError(pattern_matched=label)
                return False, label

        return True, None


class InputSanitizer:
    """Sanitizes raw text strings by stripping unsafe control chars and tags."""

    @classmethod
    def sanitize(cls, text: str | None) -> str:
        if not text:
            return ""
        # Strip null bytes and non-printable control characters (except space, tab, newline)
        cleaned = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Normalize excessive trailing/leading whitespace
        return cleaned.strip()
