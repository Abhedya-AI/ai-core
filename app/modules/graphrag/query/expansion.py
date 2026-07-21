"""expansion.py — Query Expansion logic."""

from app.modules.graphrag.query.parser import ParsedQuery


def expand_query_terms(parsed_query: ParsedQuery) -> list[str]:
    """Generate search term variants and synonyms for vector/graph search."""
    terms = [parsed_query.raw_query] + parsed_query.keywords
    synonyms = {
        "leak": ["spill", "discharge", "containment breach"],
        "risk": ["hazard", "danger", "exposure"],
        "worker": ["personnel", "operator", "technician"],
        "equipment": ["asset", "machinery", "device"],
    }
    for kw in parsed_query.keywords:
        kw_lower = kw.lower()
        if kw_lower in synonyms:
            terms.extend(synonyms[kw_lower])
    return list(dict.fromkeys(terms))
