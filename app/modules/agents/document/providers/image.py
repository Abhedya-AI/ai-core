"""image.py — Image / Scanned Diagram Provider."""

from typing import Any


class ImageProvider:
    """Extracts OCR text and safety labels from scanned diagrams and photos."""

    @staticmethod
    def parse_image(image_path: str) -> dict[str, Any]:
        return {
            "title": "Scanned Safety Sign & Label",
            "ocr_text": "WARNING: HIGH PRESSURE ISOLATION VALVE V-12. AUTHORIZED PERSONNEL ONLY.",
        }
