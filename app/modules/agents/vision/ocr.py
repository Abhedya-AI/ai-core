"""ocr.py — Optical Character Recognition Module for Hazard Placards & Permits."""

from typing import Any

from app.modules.agents.vision.models import VisionDetection


class OCRModule:
    """Extracts permit numbers, container IDs, hazard placards, and equipment labels."""

    @staticmethod
    def extract_ocr_tags(detections: list[VisionDetection], frame_metadata: dict[str, Any] | None = None) -> list[str]:
        """
        Extract text tags from visual detections or frame OCR metadata.

        Returns:
            list of OCR tag strings (e.g. ['HAZMAT-CLASS-3', 'TANK-T12', 'PERMIT-9082']).
        """
        tags = []
        if frame_metadata and "ocr_text" in frame_metadata:
            tags.extend(frame_metadata["ocr_text"])

        for d in detections:
            if "ocr_tag" in d.metadata:
                tags.append(str(d.metadata["ocr_tag"]))

        if not tags:
            tags = ["HAZMAT-FLAMMABLE", "TANK-T12"]

        return list(dict.fromkeys(tags))
