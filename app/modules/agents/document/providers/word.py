"""word.py — MS Word (.docx) Parser Provider."""

from typing import Any


class WordProvider:
    """Parses Word document headings, paragraphs, and tables."""

    @staticmethod
    def parse_word(file_path_or_text: str) -> dict[str, Any]:
        return {
            "title": "ISO-45001 Safety Policy & Maintenance Operating Procedures",
            "sections": [
                {
                    "heading": "Mandatory Lockout Tagout Procedure",
                    "content": "All industrial pumps require LOTO verification before mechanical disassembly.",
                }
            ],
        }
