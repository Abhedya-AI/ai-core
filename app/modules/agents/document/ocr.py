"""ocr.py — Phase 3: OCR Engine for Scanned Documents & Images."""

from app.modules.agents.document.providers import ImageProvider


class OCREngine:
    """Phase 3: Normalizes OCR output from scanned PDFs, warning labels, and equipment signs."""

    @staticmethod
    def process_ocr(image_path: str) -> str:
        res = ImageProvider.parse_image(image_path)
        return res.get("ocr_text", "")
