"""
app/modules/sensor/__init__.py — Sensor Intelligence Module.

Sprint 5: Full industrial sensor intelligence platform.

Architecture:
  ┌─────────────────────────────────────────────────────┐
  │                   Sensor Gateway                    │
  │  REST / Kafka / Batch → ReadingValidator → Normalizer│
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │              Feature Engineering                    │
  │  SMA · EMA · Delta · Z-Score · Spike · Drift · Trend│
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │              Multi-Engine Anomaly Detection          │
  │  Statistical · Threshold · RoC · Pattern · Correlation│
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │                  Rule Engine                        │
  │  Threshold · Time-Window · Zone · Cross-Sensor Rules │
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │              Health State Machine                   │
  │  HEALTHY→DEGRADED→WARNING→CRITICAL→OFFLINE→CALIBRATE│
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │            Analytics & Time Series Engine           │
  │  Rolling Windows · Resampling · Trend · Forecast Prep│
  └─────────────────────────┬───────────────────────────┘
                            │
  ┌────────────┬────────────▼──────────────┬────────────┐
  │  Knowledge │    GraphRAG Event         │  Digital   │
  │  Graph Sync│    Indexer Pipeline       │  Twin Layer│
  └────────────┴────────────┬──────────────┴────────────┘
                            │
  ┌─────────────────────────▼───────────────────────────┐
  │                  Supervisor Bridge                  │
  │  Typed Contracts · Risk/Emergency/Forecast routing  │
  └─────────────────────────────────────────────────────┘

Key components:
  domain/           — Immutable domain models and event factories
  application/      — Stateful services (engines, trackers, analytics)
  analysis/         — Pluggable anomaly detection engines
  infrastructure/   — Kafka publisher, Neo4j repository
  agent/            — SensorAgent (Supervisor-registered)

All downstream modules (Risk, Forecast, Vision, Hazard) consume
sensor data via the EventBus \u2014 never by direct import.
"""

from app.modules.sensor.domain.models import (
    SensorReading,
    SensorAnomaly,
    SensorHealthState,
    SensorHealth,
    AnomalyType,
    AnomalySeverity,
    ThresholdPolicy,
    ThresholdPolicyType,
    IngestionBatch,
    IngestionSource,
)
from app.modules.sensor.agent.sensor_agent import SensorAgent

__all__ = [
    "SensorReading",
    "SensorAnomaly",
    "SensorHealthState",
    "SensorHealth",
    "AnomalyType",
    "AnomalySeverity",
    "ThresholdPolicy",
    "ThresholdPolicyType",
    "IngestionBatch",
    "IngestionSource",
    "SensorAgent",
]
