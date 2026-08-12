"""types.py — Enums for Agent Runtime Lifecycle & Capabilities."""

from enum import Enum


class AgentLifecycleState(str, Enum):
    """Lifecycle states for agent execution tracking."""

    INITIALIZED = "INITIALIZED"
    VALIDATED = "VALIDATED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class Capability(str, Enum):
    """Standardized Agent Capabilities for dynamic Supervisor matching."""

    GRAPH_SEARCH = "GRAPH_SEARCH"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    VISION = "VISION"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    PREDICTION = "PREDICTION"
    ROOT_CAUSE = "ROOT_CAUSE"
    EMERGENCY = "EMERGENCY"
    EMERGENCY_RESPONSE = "EMERGENCY"
    COMPLIANCE = "COMPLIANCE"
    NOTIFICATION = "NOTIFICATION"
    SENSOR_INTELLIGENCE = "SENSOR_INTELLIGENCE"
