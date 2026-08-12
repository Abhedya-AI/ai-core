"""
schema_initializer.py — Neo4j Schema Bootstrap.

Creates all constraints and indexes required by the Knowledge Graph Platform.
All operations use IF NOT EXISTS so they are safe to call on every startup.

Called during application lifespan startup after the Neo4j driver is registered.

Returns a summary dict with counts of constraints and indexes created.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.infrastructure.neo4j.session import get_neo4j_session

log = get_logger("knowledge.schema")

# ── Entity labels that need UNIQUE id constraints ──────────────────────────────
_ENTITY_LABELS: list[str] = [
    "Plant", "Building", "Floor", "Zone",
    "Equipment", "Machine", "Asset",
    "Worker", "Contractor", "Visitor",
    "Sensor", "Camera", "Device",
    "Detection", "Reading", "Alert",
    "Hazard", "Risk", "Incident", "Emergency",
    "Workflow", "Task", "Inspection", "Maintenance",
    "PPE", "Regulation", "Policy", "Standard",
    "Document", "DocumentChunk",
    "Recommendation", "Prediction",
    "Notification", "Permit",
    "EmergencyPlan", "Weather",
    "NodeSnapshot",
]

# ── Labels that get full-text indexes on name/title/code/description ──────────
_FULLTEXT_INDEXED_LABELS: list[str] = [
    "Worker", "Contractor",
    "Equipment", "Asset",
    "Sensor", "Zone",
    "Incident", "Hazard",
    "Document", "Regulation", "Policy",
]


async def initialize_schema() -> dict[str, int | list[str]]:
    """
    Idempotently create all Neo4j constraints and indexes.

    Uses IF NOT EXISTS — safe to call on every application startup.

    Returns:
        {
            "constraints_attempted": int,
            "constraints_ok": int,
            "indexes_attempted": int,
            "indexes_ok": int,
            "errors": [str, ...],
        }
    """
    constraints_ok = 0
    indexes_ok = 0
    errors: list[str] = []

    # ── Unique ID constraints ──────────────────────────────────────────────────
    async with get_neo4j_session() as session:
        for label in _ENTITY_LABELS:
            constraint_name = f"{label.lower()}_id_unique"
            cypher = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
            try:
                await session.run(cypher)
                constraints_ok += 1
                log.debug(f"Constraint OK: {constraint_name}")
            except Exception as exc:
                err = f"Constraint {constraint_name}: {exc}"
                errors.append(err)
                log.warning(err)

    # ── Full-text composite indexes ────────────────────────────────────────────
    async with get_neo4j_session() as session:
        for label in _FULLTEXT_INDEXED_LABELS:
            index_name = f"{label.lower()}_fulltext"
            cypher = (
                f"CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON EACH [n.name, n.title, n.code, n.description]"
            )
            try:
                await session.run(cypher)
                indexes_ok += 1
                log.debug(f"Fulltext index OK: {index_name}")
            except Exception as exc:
                err = f"Fulltext index {index_name}: {exc}"
                errors.append(err)
                log.warning(err)

    # ── Composite property indexes ─────────────────────────────────────────────
    _composite_indexes: list[tuple[str, str, str]] = [
        # (index_name, label, property)
        ("incident_status_idx", "Incident", "status"),
        ("incident_severity_idx", "Incident", "severity"),
        ("hazard_severity_idx", "Hazard", "severity"),
        ("zone_risk_level_idx", "Zone", "risk_level"),
        ("equipment_status_idx", "Equipment", "status"),
        ("sensor_status_idx", "Sensor", "status"),
        ("sensor_type_idx", "Sensor", "sensor_type"),
        ("alert_status_idx", "Alert", "status"),
        ("snapshot_node_id_idx", "NodeSnapshot", "node_id"),
        ("snapshot_created_at_idx", "NodeSnapshot", "created_at"),
    ]

    async with get_neo4j_session() as session:
        for index_name, label, prop in _composite_indexes:
            cypher = (
                f"CREATE INDEX {index_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            try:
                await session.run(cypher)
                indexes_ok += 1
                log.debug(f"Property index OK: {index_name}")
            except Exception as exc:
                err = f"Property index {index_name}: {exc}"
                errors.append(err)
                log.warning(err)

    summary = {
        "constraints_attempted": len(_ENTITY_LABELS),
        "constraints_ok": constraints_ok,
        "indexes_attempted": len(_FULLTEXT_INDEXED_LABELS) + len(_composite_indexes),
        "indexes_ok": indexes_ok,
        "errors": errors,
    }

    if errors:
        log.warning(
            f"Schema initialization completed with {len(errors)} errors. "
            f"Constraints: {constraints_ok}/{len(_ENTITY_LABELS)}, "
            f"Indexes: {indexes_ok}/{len(_FULLTEXT_INDEXED_LABELS) + len(_composite_indexes)}"
        )
    else:
        log.info(
            f"Schema initialization complete. "
            f"Constraints: {constraints_ok}, Indexes: {indexes_ok}"
        )

    return summary
