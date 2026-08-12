"""memory_index.py — Fingerprint-based investigation similarity index.

Provides lightweight cosine-similarity on EvidenceFingerprint vectors
without requiring an LLM or vector database. Uses Redis sorted sets
for fast top-K retrieval.
"""
from __future__ import annotations
import json
import math
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client
from app.modules.root_cause.domain.models import Evidence, EvidenceFingerprint

log = get_logger("root_cause.memory.index")

_FINGERPRINT_KEY = "rca:memory:fingerprint:{investigation_id}"
_ALL_FINGERPRINTS_KEY = "rca:memory:all_fingerprints"


def build_fingerprint(evidence_list: list[Evidence]) -> EvidenceFingerprint:
    """Build a normalised fingerprint from an evidence list."""
    type_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    zone_ids: set[str] = set()
    equipment_ids: set[str] = set()
    total_conf = 0.0

    for ev in evidence_list:
        type_counts[ev.evidence_type.value] = type_counts.get(ev.evidence_type.value, 0) + 1
        source_counts[ev.source.value] = source_counts.get(ev.source.value, 0) + 1
        severity_counts[ev.severity] = severity_counts.get(ev.severity, 0) + 1
        if ev.zone_id:
            zone_ids.add(ev.zone_id)
        if ev.equipment_id:
            equipment_ids.add(ev.equipment_id)
        total_conf += ev.confidence

    n = len(evidence_list)
    return EvidenceFingerprint(
        evidence_type_counts=type_counts,
        source_counts=source_counts,
        severity_counts=severity_counts,
        zone_ids=list(zone_ids),
        equipment_ids=list(equipment_ids),
        total_evidence=n,
        avg_confidence=total_conf / n if n > 0 else 0.0,
    )


def _to_vector(fp: EvidenceFingerprint) -> dict[str, float]:
    """Convert fingerprint to a sparse float vector for cosine similarity."""
    vec: dict[str, float] = {}
    for k, v in fp.evidence_type_counts.items():
        vec[f"type:{k}"] = float(v)
    for k, v in fp.source_counts.items():
        vec[f"src:{k}"] = float(v)
    for k, v in fp.severity_counts.items():
        vec[f"sev:{k}"] = float(v)
    vec["total"] = float(fp.total_evidence)
    vec["confidence"] = fp.avg_confidence
    return vec


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Sparse cosine similarity between two feature vectors."""
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class MemoryIndex:
    """Redis-backed similarity index for investigation fingerprints."""

    async def index_fingerprint(
        self, investigation_id: str, fingerprint: EvidenceFingerprint
    ) -> None:
        """Store a fingerprint in Redis for future similarity queries."""
        try:
            redis = get_client()
            key = _FINGERPRINT_KEY.format(investigation_id=investigation_id)
            await redis.set(key, fingerprint.model_dump_json(), ex=86400 * 30)
            await redis.sadd(_ALL_FINGERPRINTS_KEY, investigation_id)
        except Exception as exc:
            log.warning(f"MemoryIndex: failed to index fingerprint for {investigation_id}: {exc}")

    async def find_similar(
        self, query_fingerprint: EvidenceFingerprint, top_k: int = 5, min_similarity: float = 0.3
    ) -> list[dict[str, Any]]:
        """Return top-K most similar investigation IDs with similarity scores."""
        try:
            redis = get_client()
            all_ids = await redis.smembers(_ALL_FINGERPRINTS_KEY)
            if not all_ids:
                return []
            query_vec = _to_vector(query_fingerprint)
            results: list[dict[str, Any]] = []
            for inv_id in all_ids:
                key = _FINGERPRINT_KEY.format(investigation_id=inv_id)
                raw = await redis.get(key)
                if not raw:
                    continue
                fp = EvidenceFingerprint.model_validate_json(raw)
                sim = _cosine_similarity(query_vec, _to_vector(fp))
                if sim >= min_similarity:
                    results.append({"investigation_id": inv_id, "similarity": round(sim, 4)})
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception as exc:
            log.warning(f"MemoryIndex: similarity search failed: {exc}")
            return []

    async def remove_fingerprint(self, investigation_id: str) -> None:
        """Remove a fingerprint from the index."""
        try:
            redis = get_client()
            await redis.delete(_FINGERPRINT_KEY.format(investigation_id=investigation_id))
            await redis.srem(_ALL_FINGERPRINTS_KEY, investigation_id)
        except Exception as exc:
            log.warning(f"MemoryIndex: failed to remove fingerprint: {exc}")
