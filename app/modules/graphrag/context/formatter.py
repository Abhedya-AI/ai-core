"""formatter.py — Context Formatter for LLM prompts."""

from app.modules.graphrag.ranking.fusion import FusedEvidence


def format_context_block(evidence_items: list[FusedEvidence]) -> str:
    """
    Format fused evidence items into concise, structured LLM context lines.

    Example output:
    • [GRAPH] Equipment 'Tank T-12' - Status: OPERATIONAL
    • [DOCUMENT] Safety Manual: SOP-12 Evacuation procedure...
    """
    lines = ["=== INDUSTRIAL KNOWLEDGE GRAPH & SAFETY CONTEXT ==="]
    for idx, item in enumerate(evidence_items, 1):
        lines.append(f"{idx}. [{item.source_type}] {item.content} (Score: {item.fusion_score})")
    return "\n".join(lines)
