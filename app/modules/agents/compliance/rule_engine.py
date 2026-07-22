"""rule_engine.py — Phase 2: Versioned & Reusable Compliance Rule Engine."""

from typing import Any

from pydantic import BaseModel, Field


class ComplianceRule(BaseModel):
    """Reusable versioned compliance rule definition."""

    rule_id: str
    version: str = "1.0.0"
    name: str
    regulation_code: str
    description: str
    target_operation: str = "*"


class RuleEngine:
    """Phase 2: Reusable, versioned rule engine evaluating compliance policies."""

    def __init__(self) -> None:
        self._rules: list[ComplianceRule] = [
            ComplianceRule(
                rule_id="RULE-HOTWORK-01",
                version="1.0.0",
                name="Hot Work Permit Gas Test Requirement",
                regulation_code="FS-17",
                description="Hot work operation requires valid gas test and active non-expired permit.",
                target_operation="HOT_WORK",
            ),
            ComplianceRule(
                rule_id="RULE-LOCKOUT-01",
                version="1.0.0",
                name="Lockout/Tagout Verification Sequence",
                regulation_code="OSHA-1910.147",
                description="Maintenance activity must complete Lockout verification prior to work.",
                target_operation="MAINTENANCE",
            ),
            ComplianceRule(
                rule_id="RULE-CONFINED-01",
                version="1.0.0",
                name="Confined Space Certification Requirement",
                regulation_code="HS-04",
                description="Personnel entering confined space must hold active certification.",
                target_operation="CONFINED_SPACE",
            ),
        ]

    def evaluate_rules(self, operation_type: str = "*") -> list[ComplianceRule]:
        """Return rules applicable to given operation."""
        return [
            r for r in self._rules if r.target_operation == "*" or r.target_operation.lower() in operation_type.lower() or operation_type == "*"
        ]
