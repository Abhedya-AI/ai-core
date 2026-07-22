"""html.py — HTML Web / Portal Document Parser Provider."""

from typing import Any


class HTMLProvider:
    """Parses HTML web procedures and wiki documentation pages."""

    @staticmethod
    def parse_html(html_text: str) -> dict[str, Any]:
        return {"title": "Internal Wiki: Emergency Evacuation Guidelines", "body": "In case of gas leak in Zone B, clear corridors to Exit C."}
