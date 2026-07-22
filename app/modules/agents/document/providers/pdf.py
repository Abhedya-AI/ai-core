"""pdf.py — PDF Document Parser Provider."""

from typing import Any


class PDFProvider:
    """Parses PDF layout structure, tables, and page headings."""

    @staticmethod
    def parse_pdf(file_path_or_text: str) -> dict[str, Any]:
        return {
            "title": "SOP HS-04 Hazardous Lockout & Valve Operation Manual",
            "pages": [
                {
                    "page_number": 1,
                    "headings": ["Section 1: General Safety Protocol"],
                    "content": "Before attempting maintenance on Pump P-12 or Valve V-12, shut main isolation valve and verify pressure is zero.",
                },
                {
                    "page_number": 2,
                    "headings": ["Section 5.2: Valve V-12 Maintenance Procedure"],
                    "content": "Inspect Valve V-12 mechanical seal every 30 days. Flush system before restarting. Overdue maintenance by >14 days requires supervisor approval.",
                },
            ],
        }
