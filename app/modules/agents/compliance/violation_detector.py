"""violation_detector.py — Phase 6: Multi-Source Violation Detection Engine."""

from app.modules.agents.compliance.models import ComplianceEvidence, ComplianceViolation, ViolationSeverity


class ViolationDetector:
    """Phase 6: Aggregates violations across permits, SOPs, PPE, worker certifications, and visual observations."""

    @staticmethod
    def detect_violations(
        evidence: ComplianceEvidence,
        permit_results: dict,
        sop_results: dict,
    ) -> list[ComplianceViolation]:
        """
        Detect and structure all compliance violations.

        Returns:
            list of ComplianceViolation objects.
        """
        violations: list[ComplianceViolation] = []

        # 1. Permit violations
        for pv in permit_results.get("permit_violations", []):
            violations.append(
                ComplianceViolation(
                    violation_id=pv["violation_id"],
                    violation_type=pv["violation_type"],
                    severity=ViolationSeverity[pv["severity"]],
                    affected_entity=pv["affected_entity"],
                    evidence_summary=pv["evidence_summary"],
                    regulation_reference=pv["regulation_reference"],
                )
            )

        # 2. SOP sequence violations
        for sv in sop_results.get("sop_violations", []):
            violations.append(
                ComplianceViolation(
                    violation_id=sv["violation_id"],
                    violation_type=sv["violation_type"],
                    severity=ViolationSeverity[sv["severity"]],
                    affected_entity=sv["affected_entity"],
                    evidence_summary=sv["evidence_summary"],
                    regulation_reference=sv["regulation_reference"],
                )
            )

        # 3. Worker certification violations
        for cert in evidence.worker_certifications:
            if not cert.get("valid", True):
                wid = cert.get("worker_id", "WORKER")
                ctype = cert.get("certification", "CERT")
                violations.append(
                    ComplianceViolation(
                        violation_id=f"VIO-CERT-{wid}",
                        violation_type="MISSING_WORKER_CERTIFICATION",
                        severity=ViolationSeverity.CRITICAL,
                        affected_entity=wid,
                        evidence_summary=f"Worker '{wid}' lacks valid '{ctype}' certification.",
                        regulation_reference="HS-04",
                    )
                )

        # 4. Vision observation violations (e.g. Blocked exit / PPE)
        for vobs in evidence.vision_observations:
            obs = vobs.get("observation", "")
            if "BLOCKED_EMERGENCY_EXIT" in obs:
                violations.append(
                    ComplianceViolation(
                        violation_id=f"VIO-EXIT-{vobs.get('zone_id', 'ZONE')}",
                        violation_type="BLOCKED_EMERGENCY_EXIT",
                        severity=ViolationSeverity.CRITICAL,
                        affected_entity=vobs.get("zone_id", "ZONE"),
                        evidence_summary=f"CCTV camera '{vobs.get('camera_id')}' detected blocked emergency exit in '{vobs.get('zone_id')}'.",
                        regulation_reference="OSHA-1910.37",
                    )
                )
            elif "MISSING_HELMET" in obs:
                violations.append(
                    ComplianceViolation(
                        violation_id=f"VIO-PPE-{vobs.get('worker_id', 'WORKER')}",
                        violation_type="PPE_HELMET_MISSING",
                        severity=ViolationSeverity.MAJOR,
                        affected_entity=vobs.get("worker_id", "WORKER"),
                        evidence_summary=f"CCTV detected worker '{vobs.get('worker_id')}' without helmet.",
                        regulation_reference="OSHA-1910.135",
                    )
                )

        return violations
