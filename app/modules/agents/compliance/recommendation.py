"""recommendation.py — Categorized Action Recommendation Engine."""

from app.modules.agents.compliance.models import ComplianceViolation, ViolationSeverity


class ComplianceRecommendationEngine:
    """Generates prioritized recommendations categorized by urgency (Immediate, Short-Term, Long-Term)."""

    @staticmethod
    def generate_recommendations(violations: list[ComplianceViolation]) -> tuple[list[str], dict[str, list[str]]]:
        """
        Generate categorized corrective recommendations.

        Returns:
            tuple[flattened_list, categorized_dict]
        """
        immediate = []
        short_term = []
        long_term = []

        for v in violations:
            if v.violation_type == "EXPIRED_PERMIT":
                immediate.append("Suspend hot work operations immediately until permit revalidation.")
                short_term.append("Renew hot work permit and conduct fresh gas level test.")
            elif v.violation_type == "SOP_SEQUENCE_SKIPPED":
                immediate.append("Halt maintenance activity until Lockout verification is completed.")
                short_term.append("Re-execute SOP-LOCKOUT-01 from step 1.")
            elif v.violation_type == "BLOCKED_EMERGENCY_EXIT":
                immediate.append("Clear emergency exit obstruction in affected zone immediately.")
            elif v.violation_type == "MISSING_WORKER_CERTIFICATION":
                immediate.append(f"Reassign worker '{v.affected_entity}' outside confined space zone.")
                short_term.append(f"Schedule confined-space safety certification training for '{v.affected_entity}'.")

        long_term.append("Audit facility SOP workflows and digitize permit sign-off gates.")
        long_term.append("Update worker safety certification tracking database.")

        categorized = {
            "Immediate": list(dict.fromkeys(immediate)),
            "Short-Term": list(dict.fromkeys(short_term)),
            "Long-Term": list(dict.fromkeys(long_term)),
        }

        flattened = categorized["Immediate"] + categorized["Short-Term"] + categorized["Long-Term"]
        return flattened, categorized
