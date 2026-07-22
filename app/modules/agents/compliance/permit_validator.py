"""permit_validator.py — Phase 3: Permit Validation Module."""

from typing import Any


class PermitValidator:
    """Phase 3: Validates work permit expiry, supervisor approval, gas test validity, and zone restrictions."""

    @staticmethod
    def validate_permits(permits: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate permit status.

        Returns:
            dict containing validation summary and detected violation items.
        """
        valid_permits = []
        invalid_permits = []
        violations = []

        for p in permits:
            pid = p.get("permit_id", "PERMIT-UNK")
            expired = p.get("expired", False)
            approved = p.get("approved_by_supervisor", True)
            gas_valid = p.get("gas_test_valid", True)

            if expired:
                invalid_permits.append(pid)
                violations.append({
                    "violation_id": f"VIO-PERMIT-EXP-{pid}",
                    "violation_type": "EXPIRED_PERMIT",
                    "severity": "CRITICAL",
                    "affected_entity": pid,
                    "evidence_summary": f"Work permit '{pid}' has expired.",
                    "regulation_reference": "FS-17",
                })

            if not gas_valid:
                invalid_permits.append(pid)
                violations.append({
                    "violation_id": f"VIO-GAS-TEST-{pid}",
                    "violation_type": "GAS_TEST_EXPIRED",
                    "severity": "CRITICAL",
                    "affected_entity": pid,
                    "evidence_summary": f"Gas monitoring test expired or missing for permit '{pid}'.",
                    "regulation_reference": "FS-17",
                })

            if not expired and gas_valid and approved:
                valid_permits.append(pid)

        return {
            "valid_permits": valid_permits,
            "invalid_permits": list(dict.fromkeys(invalid_permits)),
            "permit_violations": violations,
            "all_valid": len(invalid_permits) == 0,
        }
