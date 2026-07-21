"""ppe.py — PPE Compliance Evaluation Module."""

from app.modules.agents.vision.models import VisionDetection


class PPEModule:
    """Evaluates PPE compliance (Helmet, Vest, Gloves, Boots, Goggles) for tracked personnel."""

    @staticmethod
    def evaluate_compliance(detections: list[VisionDetection]) -> list[str]:
        """
        Evaluate PPE compliance from visual detections.

        Returns:
            list of PPE violation description strings.
        """
        violations = []
        labels = [d.label.lower() for d in detections]

        person_detected = any("person" in l or "worker" in l for l in labels)
        if person_detected:
            if not any("helmet" in l or "hard_hat" in l for l in labels):
                violations.append("Missing Helmet (PPE Violation)")
            if not any("vest" in l or "hi_vis" in l for l in labels):
                violations.append("Missing Safety Vest (PPE Violation)")

        for label in labels:
            if "ppe_helmet_missing" in label or "missing_helmet" in label:
                violations.append("Missing Helmet (PPE Violation)")
            if "ppe_gloves_missing" in label or "missing_gloves" in label:
                violations.append("Missing Gloves (PPE Violation)")

        return list(dict.fromkeys(violations))
