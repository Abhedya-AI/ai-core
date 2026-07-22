"""sop_validator.py — Phase 4: SOP Sequence Validation Module."""

from typing import Any


class SOPValidator:
    """Phase 4: Validates procedural sequence execution (Shutdown -> Isolation -> Lockout -> Verification -> Maintenance)."""

    @staticmethod
    def validate_sop_sequences(sops: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate SOP step execution sequence.

        Returns:
            dict containing SOP validation summary and sequence violation items.
        """
        skipped_steps = []
        violations = []

        for sop in sops:
            sop_id = sop.get("sop_id", "SOP-01")
            req_seq = sop.get("required_sequence", ["Shutdown", "Isolation", "Lockout", "Verification", "Maintenance"])
            exec_seq = sop.get("executed_sequence", [])

            # Check if required steps were skipped before Maintenance
            missing = [step for step in req_seq if step not in exec_seq]
            if missing:
                skipped_steps.extend(missing)
                violations.append({
                    "violation_id": f"VIO-SOP-SEQ-{sop_id}",
                    "violation_type": "SOP_SEQUENCE_SKIPPED",
                    "severity": "CRITICAL" if "Lockout" in missing else "MAJOR",
                    "affected_entity": sop_id,
                    "evidence_summary": f"SOP '{sop_id}' skipped mandatory sequence step(s): {', '.join(missing)}.",
                    "regulation_reference": "OSHA-1910.147",
                })

        return {
            "skipped_steps": list(dict.fromkeys(skipped_steps)),
            "sop_violations": violations,
            "sequence_valid": len(skipped_steps) == 0,
        }
