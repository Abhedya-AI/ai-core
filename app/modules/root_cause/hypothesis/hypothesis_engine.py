"""hypothesis_engine.py — Multi-Hypothesis Generation and Analysis Engine."""
from __future__ import annotations
import uuid
from collections import defaultdict

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, CausalChain, Hypothesis, HypothesisScore, HypothesisStatus,
    PrimaryCause, ContributingFactor,
)

log = get_logger("root_cause.hypothesis")


class HypothesisEngine:
    """Generates, ranks, evaluates, and eliminates investigation hypotheses."""

    def generate_hypotheses(
        self, evidence_list: list[Evidence], causal_chain: CausalChain, investigation_id: str,
    ) -> list[Hypothesis]:
        log.info(f"Generating hypotheses for investigation {investigation_id}")
        clusters: dict[str, list[Evidence]] = defaultdict(list)
        for ev in evidence_list:
            key = f"{ev.equipment_id or 'none'}_{ev.zone_id or 'none'}_{ev.severity}"
            clusters[key].append(ev)

        hypotheses: list[Hypothesis] = []
        for key, cluster in clusters.items():
            if not cluster:
                continue
            parts = key.split("_")
            equip = parts[0] if parts[0] != "none" else "system"
            zone = parts[1] if len(parts) > 1 and parts[1] != "none" else "unknown"
            ev_count = len(cluster)
            base_conf = min(0.9, 0.4 + ev_count * 0.1)

            # Causal graph support
            graph_entity_ids = {n.entity_id for n in causal_chain.nodes}
            supported = sum(1 for e in cluster if e.id in graph_entity_ids)
            graph_score = supported / ev_count if ev_count > 0 else 0.0
            overall = base_conf * 0.6 + graph_score * 0.4

            score = HypothesisScore(
                probability=base_conf,
                supporting_evidence_count=ev_count,
                contradicting_evidence_count=0,
                graph_support_score=graph_score,
                historical_match_score=0.0,
                overall_confidence=overall,
            )
            hyp = Hypothesis(
                investigation_id=investigation_id,
                title=f"Failure cluster — equipment {equip}, zone {zone}",
                description=f"Hypothesis based on {ev_count} evidence items in equipment {equip}, zone {zone}.",
                status=HypothesisStatus.GENERATED,
                score=score,
                supporting_evidence_ids=[e.id for e in cluster],
                affected_equipment_ids=[equip] if equip != "system" else [],
                affected_zone_ids=[zone] if zone != "unknown" else [],
            )
            hypotheses.append(hyp)
        return hypotheses

    def rank_hypotheses(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        ranked = sorted(
            hypotheses, key=lambda h: h.score.overall_confidence, reverse=True,
        )
        for idx, h in enumerate(ranked):
            h.rank = idx + 1
            if idx == 0 and h.score.overall_confidence > 0.6:
                h.status = HypothesisStatus.CONFIRMED
        return ranked

    def evaluate_hypothesis(
        self, hypothesis: Hypothesis, evidence_list: list[Evidence],
    ) -> Hypothesis:
        for ev in evidence_list:
            if ev.severity in ("HIGH", "CRITICAL"):
                if ev.id not in hypothesis.supporting_evidence_ids:
                    hypothesis.supporting_evidence_ids.append(ev.id)
            elif ev.id not in hypothesis.contradicting_evidence_ids:
                hypothesis.contradicting_evidence_ids.append(ev.id)
        supp = len(hypothesis.supporting_evidence_ids)
        contra = len(hypothesis.contradicting_evidence_ids)
        total = supp + contra
        if total > 0:
            hypothesis.score.overall_confidence = max(0.1, min(0.99, supp / total))
            hypothesis.score.supporting_evidence_count = supp
            hypothesis.score.contradicting_evidence_count = contra
        return hypothesis

    def eliminate_hypothesis(self, hypothesis: Hypothesis, reason: str) -> Hypothesis:
        hypothesis.status = HypothesisStatus.REJECTED
        hypothesis.rejection_reason = reason
        return hypothesis

    def confirm_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        hypothesis.status = HypothesisStatus.CONFIRMED
        return hypothesis

    def find_primary_cause(self, hypotheses: list[Hypothesis]) -> PrimaryCause | None:
        confirmed = [h for h in hypotheses if h.status == HypothesisStatus.CONFIRMED]
        if not confirmed:
            # Fallback: use top ranked
            ranked = sorted(hypotheses, key=lambda h: h.rank if h.rank > 0 else 999)
            if ranked:
                top = ranked[0]
                return PrimaryCause(
                    hypothesis_id=top.id,
                    description=top.description,
                    confidence=top.score.overall_confidence,
                    evidence_ids=top.supporting_evidence_ids[:5],
                )
            return None
        top = sorted(confirmed, key=lambda h: h.rank)[0]
        return PrimaryCause(
            hypothesis_id=top.id,
            description=top.description,
            confidence=top.score.overall_confidence,
            evidence_ids=top.supporting_evidence_ids[:5],
        )

    def find_contributing_factors(
        self, hypotheses: list[Hypothesis], evidence_list: list[Evidence],
    ) -> list[ContributingFactor]:
        factors: list[ContributingFactor] = []
        valid = [
            h for h in hypotheses
            if h.status in (HypothesisStatus.CONFIRMED, HypothesisStatus.GENERATED)
        ]
        # Skip the top-ranked (primary cause), take the rest
        secondary = sorted(valid, key=lambda h: h.rank if h.rank > 0 else 999)[1:]
        for h in secondary:
            if h.score.overall_confidence > 0.3:
                factors.append(ContributingFactor(
                    description=f"Contributing factor: {h.title}",
                    factor_type=h.affected_equipment_ids[0] if h.affected_equipment_ids else "process",
                    confidence=h.score.overall_confidence,
                    evidence_ids=h.supporting_evidence_ids[:3],
                    mitigation=f"Review and address conditions described in: {h.title}",
                ))
        return factors
