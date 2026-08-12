"""pattern_library.py — 9-pattern seeded industrial failure pattern library."""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import FailurePattern, PatternType

log = get_logger("root_cause.patterns.library")

# ──────────────────────────────────────────────────────────────────────
# SEEDED INDUSTRIAL FAILURE PATTERNS (production-grade definitions)
# ──────────────────────────────────────────────────────────────────────

_SEEDED_PATTERNS: list[dict[str, Any]] = [
    {
        "name": "Gas Leak",
        "pattern_type": PatternType.GAS_LEAK,
        "description": "Uncontrolled release of gas from equipment, pipes, or storage vessels. "
                       "Typically detected by gas sensors, odour complaints, and pressure drops.",
        "trigger_conditions": [
            "Gas sensor threshold exceeded",
            "Pressure drop in pipeline > 15%",
            "Multiple sensor readings anomalous",
            "Worker PPE violation in hazardous zone",
        ],
        "causal_chain_template": [
            "Equipment seal failure or corrosion",
            "Pressure increase beyond rated capacity",
            "Gas release through leak point",
            "Sensor detection and alert",
            "Potential ignition risk",
        ],
        "prior_probability": 0.12,
        "required_evidence_types": ["SENSOR_READING", "AUDIT_LOG"],
        "required_sources": ["SENSOR_INTELLIGENCE"],
        "typical_severity": "CRITICAL",
        "typical_equipment_types": ["PIPE", "VALVE", "COMPRESSOR", "STORAGE_VESSEL"],
    },
    {
        "name": "Pressure Failure",
        "pattern_type": PatternType.PRESSURE_FAILURE,
        "description": "Abnormal pressure buildup or loss in pressurised systems, leading to "
                       "equipment damage or rupture.",
        "trigger_conditions": [
            "Pressure sensor reading > 120% rated",
            "Relief valve actuation",
            "Abnormal temperature correlation with pressure",
            "Maintenance overdue on pressure vessel",
        ],
        "causal_chain_template": [
            "Blocked outlet or valve failure",
            "Pressure accumulation",
            "Safety system activation or bypass",
            "Structural stress on vessel",
            "Rupture or controlled relief",
        ],
        "prior_probability": 0.09,
        "required_evidence_types": ["SENSOR_READING", "MAINTENANCE_RECORD"],
        "required_sources": ["SENSOR_INTELLIGENCE", "KNOWLEDGE_GRAPH"],
        "typical_severity": "HIGH",
        "typical_equipment_types": ["PRESSURE_VESSEL", "BOILER", "PIPELINE"],
    },
    {
        "name": "Boiler Explosion",
        "pattern_type": PatternType.BOILER_EXPLOSION,
        "description": "Catastrophic boiler failure due to over-pressure, overheating, "
                       "or water level control failure. High fatality risk.",
        "trigger_conditions": [
            "Temperature > 95% of rated limit",
            "Pressure > 110% of rated limit",
            "Water level sensor anomaly",
            "Combustion control failure",
            "Safety valve failure or bypass",
        ],
        "causal_chain_template": [
            "Water level drops below safe minimum",
            "Overheating of heat exchange surfaces",
            "Pressure builds beyond safety valve rating",
            "Structural failure of pressure vessel",
            "Explosion and steam release",
        ],
        "prior_probability": 0.04,
        "required_evidence_types": ["SENSOR_READING", "MAINTENANCE_RECORD", "AUDIT_LOG"],
        "required_sources": ["SENSOR_INTELLIGENCE", "KNOWLEDGE_GRAPH"],
        "typical_severity": "CRITICAL",
        "typical_equipment_types": ["BOILER", "STEAM_GENERATOR"],
    },
    {
        "name": "Electrical Fire",
        "pattern_type": PatternType.ELECTRICAL_FIRE,
        "description": "Fire originating from electrical faults: overloaded circuits, "
                       "insulation failure, arcing, or overheating electrical components.",
        "trigger_conditions": [
            "Overtemperature on electrical panel",
            "Smoke detection sensor triggered",
            "Current overload event logged",
            "Vision system detects smoke or flame",
        ],
        "causal_chain_template": [
            "Circuit overload or short circuit",
            "Insulation degradation",
            "Arcing or sparking",
            "Ignition of nearby materials",
            "Fire propagation",
        ],
        "prior_probability": 0.08,
        "required_evidence_types": ["SENSOR_READING", "VISION_DETECTION"],
        "required_sources": ["SENSOR_INTELLIGENCE", "VISION_INTELLIGENCE"],
        "typical_severity": "CRITICAL",
        "typical_equipment_types": ["ELECTRICAL_PANEL", "MOTOR", "TRANSFORMER"],
    },
    {
        "name": "Worker Injury",
        "pattern_type": PatternType.WORKER_INJURY,
        "description": "Physical injury to a worker caused by unsafe conditions, "
                       "PPE violation, equipment malfunction, or human error.",
        "trigger_conditions": [
            "PPE violation detected by vision",
            "Worker in restricted zone",
            "Emergency alert raised by worker",
            "Medical response request",
        ],
        "causal_chain_template": [
            "Unsafe condition or PPE non-compliance",
            "Worker exposure to hazard",
            "Physical contact with hazardous element",
            "Injury occurrence and alert",
        ],
        "prior_probability": 0.15,
        "required_evidence_types": ["VISION_DETECTION", "INCIDENT_REPORT"],
        "required_sources": ["VISION_INTELLIGENCE", "INCIDENT_MANAGEMENT"],
        "typical_severity": "HIGH",
        "typical_equipment_types": ["GENERAL"],
    },
    {
        "name": "Equipment Failure",
        "pattern_type": PatternType.EQUIPMENT_FAILURE,
        "description": "Mechanical or functional failure of industrial equipment due to "
                       "wear, overuse, maintenance neglect, or manufacturing defect.",
        "trigger_conditions": [
            "Vibration sensor anomaly",
            "Temperature out of range",
            "Maintenance overdue > 30 days",
            "Equipment status FAULT in knowledge graph",
        ],
        "causal_chain_template": [
            "Wear accumulation or defect",
            "Operating beyond design parameters",
            "Component failure",
            "Equipment shutdown or malfunction",
        ],
        "prior_probability": 0.20,
        "required_evidence_types": ["SENSOR_READING", "MAINTENANCE_RECORD", "GRAPH_ENTITY"],
        "required_sources": ["SENSOR_INTELLIGENCE", "KNOWLEDGE_GRAPH"],
        "typical_severity": "HIGH",
        "typical_equipment_types": ["MOTOR", "PUMP", "COMPRESSOR", "CONVEYOR"],
    },
    {
        "name": "Chemical Spill",
        "pattern_type": PatternType.CHEMICAL_SPILL,
        "description": "Uncontrolled release of hazardous chemicals, posing contamination, "
                       "fire, or health risks to workers and environment.",
        "trigger_conditions": [
            "Chemical sensor threshold exceeded",
            "Tank level drop without scheduled use",
            "Hazardous material alert",
            "Vision detection of liquid pooling",
        ],
        "causal_chain_template": [
            "Containment failure or valve leak",
            "Chemical release into environment",
            "Sensor and vision detection",
            "Emergency protocol activation",
        ],
        "prior_probability": 0.06,
        "required_evidence_types": ["SENSOR_READING", "VISION_DETECTION"],
        "required_sources": ["SENSOR_INTELLIGENCE", "VISION_INTELLIGENCE"],
        "typical_severity": "CRITICAL",
        "typical_equipment_types": ["STORAGE_TANK", "PIPELINE", "CHEMICAL_REACTOR"],
    },
    {
        "name": "Sensor Failure",
        "pattern_type": PatternType.SENSOR_FAILURE,
        "description": "Failure or degradation of industrial sensors causing missed detections, "
                       "false alarms, or data gaps that compromise safety monitoring.",
        "trigger_conditions": [
            "Sensor offline or no-data event",
            "Reading outside physically possible range",
            "Calibration drift detected",
            "Multiple sensors in same zone reporting zero",
        ],
        "causal_chain_template": [
            "Sensor hardware degradation or failure",
            "Communication link loss or power failure",
            "Missing sensor data in monitoring system",
            "Delayed or missed hazard detection",
        ],
        "prior_probability": 0.10,
        "required_evidence_types": ["SENSOR_READING", "AUDIT_LOG"],
        "required_sources": ["SENSOR_INTELLIGENCE", "AUDIT_FRAMEWORK"],
        "typical_severity": "MEDIUM",
        "typical_equipment_types": ["SENSOR"],
    },
    {
        "name": "Vision System Failure",
        "pattern_type": PatternType.VISION_FAILURE,
        "description": "Failure of camera or AI vision pipeline, causing blind spots in "
                       "worker safety monitoring, PPE compliance, or area surveillance.",
        "trigger_conditions": [
            "Camera offline event",
            "Vision detection count drops to zero",
            "Stream quality below threshold",
            "Model confidence consistently low",
        ],
        "causal_chain_template": [
            "Camera hardware failure or obstruction",
            "Network connectivity issue",
            "Vision AI model degradation",
            "Safety monitoring gap created",
        ],
        "prior_probability": 0.07,
        "required_evidence_types": ["VISION_DETECTION", "AUDIT_LOG"],
        "required_sources": ["VISION_INTELLIGENCE", "AUDIT_FRAMEWORK"],
        "typical_severity": "MEDIUM",
        "typical_equipment_types": ["CAMERA"],
    },
]


class PatternLibrary:
    """In-memory + Redis pattern library with seeded industrial failure patterns."""

    def __init__(self) -> None:
        self._patterns: dict[str, FailurePattern] = {}
        self._seed()

    def _seed(self) -> None:
        """Initialise with production-grade seeded patterns."""
        for data in _SEEDED_PATTERNS:
            pattern = FailurePattern(**data, is_seeded=True)
            self._patterns[pattern.id] = pattern
        log.info(f"PatternLibrary seeded with {len(self._patterns)} industrial patterns")

    def get_pattern(self, pattern_id: str) -> FailurePattern | None:
        return self._patterns.get(pattern_id)

    def get_pattern_by_type(self, pattern_type: PatternType) -> FailurePattern | None:
        for p in self._patterns.values():
            if p.pattern_type == pattern_type:
                return p
        return None

    def list_patterns(self, limit: int = 50, offset: int = 0) -> list[FailurePattern]:
        all_patterns = list(self._patterns.values())
        return all_patterns[offset : offset + limit]

    def add_pattern(self, pattern: FailurePattern) -> FailurePattern:
        self._patterns[pattern.id] = pattern
        log.info(f"Pattern '{pattern.name}' added to library")
        return pattern

    def update_pattern_confidence(self, pattern_id: str, new_confidence: float) -> bool:
        p = self._patterns.get(pattern_id)
        if not p:
            return False
        p.confidence_score = max(0.0, min(1.0, new_confidence))
        return True

    def update_historical_matches(self, pattern_id: str, increment: int = 1) -> bool:
        p = self._patterns.get(pattern_id)
        if not p:
            return False
        p.historical_matches += increment
        # Update prior probability using Laplace smoothing
        total = sum(pat.historical_matches for pat in self._patterns.values())
        if total > 0:
            p.prior_probability = (p.historical_matches + 1) / (total + len(self._patterns))
        return True

    def count(self) -> int:
        return len(self._patterns)
