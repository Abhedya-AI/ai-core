"""
timeline_engine.py — Investigation Timeline Construction and Analysis Engine.

Builds chronological event timelines from evidence, detects gaps,
correlates temporally co-occurring events, and supports filtered views.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, EvidenceSource, TimelineEvent, TimelineSequence,
)

log = get_logger("root_cause.timeline")


class TimelineEngine:
    """Constructs and analyzes investigation timelines from evidence."""

    def construct_timeline(
        self, evidence_list: list[Evidence], investigation_id: str,
    ) -> TimelineSequence:
        log.info(f"Constructing timeline for investigation {investigation_id}")
        sorted_evidence = sorted(evidence_list, key=lambda e: e.timestamp)
        events: list[TimelineEvent] = []
        for ev in sorted_evidence:
            events.append(TimelineEvent(
                timestamp=ev.timestamp,
                event_type=ev.evidence_type.value,
                source=ev.source,
                title=ev.title,
                description=ev.description,
                severity=ev.severity,
                evidence_ids=[ev.id],
                zone_id=ev.zone_id,
                equipment_id=ev.equipment_id,
                worker_id=ev.worker_id,
                is_anomalous=ev.severity in ("CRITICAL", "HIGH"),
            ))
        start = events[0].timestamp if events else datetime.now(timezone.utc).isoformat()
        end = events[-1].timestamp if events else start
        duration = self._compute_duration(start, end)
        return TimelineSequence(
            investigation_id=investigation_id,
            events=events,
            start_time=start,
            end_time=end,
            duration_seconds=duration,
        )

    def detect_missing_events(
        self, timeline: TimelineSequence, expected_interval_seconds: float,
    ) -> list[dict[str, Any]]:
        log.info("Detecting missing events in timeline")
        gaps: list[dict[str, Any]] = []
        events = timeline.events
        for i in range(1, len(events)):
            prev_ts = events[i - 1].timestamp
            curr_ts = events[i].timestamp
            diff = self._compute_duration(prev_ts, curr_ts)
            if diff > expected_interval_seconds:
                gaps.append({
                    "start_gap": prev_ts,
                    "end_gap": curr_ts,
                    "duration_seconds": diff,
                    "previous_event_id": events[i - 1].id,
                    "next_event_id": events[i].id,
                })
        return gaps

    def correlate_events(
        self, timeline: TimelineSequence, correlation_window_seconds: float,
    ) -> TimelineSequence:
        log.info("Correlating events in timeline")
        events = timeline.events
        if not events:
            return timeline

        groups: list[list[TimelineEvent]] = []
        current_group: list[TimelineEvent] = [events[0]]
        for evt in events[1:]:
            diff = self._compute_duration(current_group[0].timestamp, evt.timestamp)
            if diff <= correlation_window_seconds:
                current_group.append(evt)
            else:
                groups.append(current_group)
                current_group = [evt]
        groups.append(current_group)

        # Assign correlation groups
        parallel_groups: list[list[str]] = []
        for gidx, group in enumerate(groups):
            if len(group) > 1:
                group_id = f"corr-{gidx}"
                for evt in group:
                    evt.correlation_group = group_id
                parallel_groups.append([evt.id for evt in group])

        return TimelineSequence(
            investigation_id=timeline.investigation_id,
            events=[evt for g in groups for evt in g],
            start_time=timeline.start_time,
            end_time=timeline.end_time,
            duration_seconds=timeline.duration_seconds,
            parallel_event_groups=parallel_groups,
        )

    def filter_by_time_window(
        self, timeline: TimelineSequence, start: str, end: str,
    ) -> TimelineSequence:
        log.info(f"Filtering timeline from {start} to {end}")
        filtered = [e for e in timeline.events if start <= e.timestamp <= end]
        s = filtered[0].timestamp if filtered else start
        e = filtered[-1].timestamp if filtered else end
        return TimelineSequence(
            investigation_id=timeline.investigation_id,
            events=filtered,
            start_time=s,
            end_time=e,
            duration_seconds=self._compute_duration(s, e),
        )

    def merge_timelines(
        self, timelines: list[TimelineSequence],
    ) -> TimelineSequence:
        log.info("Merging multiple timelines")
        if not timelines:
            now = datetime.now(timezone.utc).isoformat()
            return TimelineSequence(investigation_id="merged", start_time=now, end_time=now)

        all_events: list[TimelineEvent] = []
        for t in timelines:
            all_events.extend(t.events)
        seen: set[str] = set()
        unique: list[TimelineEvent] = []
        for evt in all_events:
            if evt.id not in seen:
                seen.add(evt.id)
                unique.append(evt)
        unique.sort(key=lambda e: e.timestamp)
        inv_id = timelines[0].investigation_id
        s = unique[0].timestamp if unique else datetime.now(timezone.utc).isoformat()
        e = unique[-1].timestamp if unique else s
        return TimelineSequence(
            investigation_id=inv_id,
            events=unique,
            start_time=s,
            end_time=e,
            duration_seconds=self._compute_duration(s, e),
        )

    def build_equipment_timeline(
        self, evidence_list: list[Evidence], equipment_id: str,
    ) -> TimelineSequence:
        log.info(f"Building timeline for equipment {equipment_id}")
        filtered = [e for e in evidence_list if e.equipment_id == equipment_id]
        return self.construct_timeline(filtered, f"equip_{equipment_id}")

    def build_zone_timeline(
        self, evidence_list: list[Evidence], zone_id: str,
    ) -> TimelineSequence:
        log.info(f"Building timeline for zone {zone_id}")
        filtered = [e for e in evidence_list if e.zone_id == zone_id]
        return self.construct_timeline(filtered, f"zone_{zone_id}")

    def build_worker_timeline(
        self, evidence_list: list[Evidence], worker_id: str,
    ) -> TimelineSequence:
        log.info(f"Building timeline for worker {worker_id}")
        filtered = [e for e in evidence_list if e.worker_id == worker_id]
        return self.construct_timeline(filtered, f"worker_{worker_id}")

    @staticmethod
    def _compute_duration(start_iso: str, end_iso: str) -> float:
        try:
            s = datetime.fromisoformat(start_iso)
            e = datetime.fromisoformat(end_iso)
            return max(0.0, (e - s).total_seconds())
        except (ValueError, TypeError):
            return 0.0
