"""
neo4j/cypher.py — Cypher query constants.

This file will grow as the Knowledge Graph module is built.
Currently a placeholder: no business logic, no graph queries.

Convention:
  - Group queries by domain (SENSOR_, WORKER_, RISK_, etc.)
  - Use UPPERCASE_SNAKE for constants
  - Always use parameterized queries ($param) — never f-strings in Cypher

Example (future use):
    from app.infrastructure.neo4j.cypher import SENSOR_GET_BY_ID
    await session.run(SENSOR_GET_BY_ID, sensor_id="S-001")
"""

# ── Connectivity ───────────────────────────────────────────────────────────────
HEALTH_CHECK = "RETURN 1 AS ok"

# ── Constraints (run during startup) ──────────────────────────────────────────
CREATE_SENSOR_CONSTRAINT = """
CREATE CONSTRAINT sensor_id_unique IF NOT EXISTS
FOR (s:Sensor) REQUIRE s.id IS UNIQUE
"""

CREATE_WORKER_CONSTRAINT = """
CREATE CONSTRAINT worker_id_unique IF NOT EXISTS
FOR (w:Worker) REQUIRE w.id IS UNIQUE
"""
