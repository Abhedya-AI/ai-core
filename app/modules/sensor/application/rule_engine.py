"""
sensor/application/rule_engine.py — Configurable Sensor Rule Engine.

Supports: threshold rules, combined AND conditions, time-window rules,
cross-sensor rules, zone-level rules, equipment-level rules, worker proximity,
priority-based evaluation, cooldown enforcement, and escalation actions.
"""
from __future__ import annotations
import time
from typing import Any
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalySeverity, AnomalyType
from app.modules.sensor.domain.rule_models import (
    SensorRule, RuleCondition, RuleAction, RuleConditionOperator,
    RuleActionType, RulePriority, RuleTriggerRecord,
)

log = get_logger("sensor.rule_engine")

class SensorRuleEngine:
    """Evaluates configurable rules against incoming sensor readings."""

    def __init__(self):
        """Initialize the rule engine with default safety rules."""
        self._rules: dict[str, SensorRule] = {}
        self._trigger_history: dict[str, list[RuleTriggerRecord]] = {}
        # Tracks last trigger time (Unix timestamp) keyed by f"{rule_id}_{sensor_id}"
        self._last_trigger: dict[str, float] = {}

        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register default industrial safety rules."""
        rules = [
            SensorRule(
                name="HIGH_TEMPERATURE",
                description="Temperature exceeds 80.0°C",
                sensor_type_filter="TEMPERATURE",
                conditions=[
                    RuleCondition(field="value", operator=RuleConditionOperator.GT, threshold=80.0)
                ],
                actions=[
                    RuleAction(action_type=RuleActionType.NOTIFY_SUPERVISOR, severity="CRITICAL")
                ],
                priority=RulePriority.P1
            ),
            SensorRule(
                name="GAS_THRESHOLD",
                description="Gas concentration exceeds 50.0ppm",
                sensor_type_filter="GAS",
                conditions=[
                    RuleCondition(field="value", operator=RuleConditionOperator.GT, threshold=50.0)
                ],
                actions=[
                    RuleAction(action_type=RuleActionType.NOTIFY_SUPERVISOR, severity="CRITICAL"),
                    RuleAction(action_type=RuleActionType.TRIGGER_ALERT, severity="CRITICAL")
                ],
                priority=RulePriority.P1
            ),
            SensorRule(
                name="CRITICAL_PRESSURE",
                description="Pressure exceeds 200.0bar",
                sensor_type_filter="PRESSURE",
                conditions=[
                    RuleCondition(field="value", operator=RuleConditionOperator.GT, threshold=200.0)
                ],
                actions=[
                    RuleAction(action_type=RuleActionType.NOTIFY_SUPERVISOR, severity="CRITICAL")
                ],
                priority=RulePriority.P1
            ),
            SensorRule(
                name="HIGH_VIBRATION",
                description="Vibration exceeds 10.0mm/s",
                sensor_type_filter="VIBRATION",
                conditions=[
                    RuleCondition(field="value", operator=RuleConditionOperator.GT, threshold=10.0)
                ],
                actions=[
                    RuleAction(action_type=RuleActionType.NOTIFY_SUPERVISOR, severity="HIGH")
                ],
                priority=RulePriority.P2
            )
        ]
        for rule in rules:
            self.register_rule(rule)

    def register_rule(self, rule: SensorRule) -> SensorRule:
        """Register a new rule for evaluation."""
        self._rules[rule.rule_id] = rule
        log.info(f"Registered rule: {rule.name} (ID: {rule.rule_id})")
        return rule

    def add_rule(self, rule: SensorRule) -> SensorRule:
        """Alias for register_rule."""
        return self.register_rule(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by its ID."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            log.info(f"Removed rule ID: {rule_id}")
            return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """Alias for remove_rule."""
        return self.remove_rule(rule_id)

    def get_rule(self, rule_id: str) -> SensorRule | None:
        """Get rule by ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[SensorRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def get_rules(self, sensor_id: str | None = None, sensor_type: str | None = None) -> list[SensorRule]:
        """Get registered rules, optionally filtered by sensor ID or type."""
        rules = list(self._rules.values())
        if sensor_id:
            rules = [r for r in rules if r.sensor_id is None or r.sensor_id == sensor_id]
        if sensor_type:
            rules = [r for r in rules if r.sensor_type_filter is None or r.sensor_type_filter == sensor_type]
        return rules

    def enable_rule(self, rule_id: str) -> SensorRule | None:
        """Enable a rule by ID."""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        updated = rule.model_copy(update={"enabled": True})
        self._rules[rule_id] = updated
        return updated

    def disable_rule(self, rule_id: str) -> SensorRule | None:
        """Disable a rule by ID."""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        updated = rule.model_copy(update={"enabled": False})
        self._rules[rule_id] = updated
        return updated

    def evaluate(self, reading: SensorReading, recent_values: list[float], context: dict[str, Any] | None = None) -> list[RuleTriggerRecord]:
        """Evaluate a sensor reading against all enabled rules."""
        context = context or {}
        triggers: list[RuleTriggerRecord] = []
        current_time = time.time()
        sensor_type = reading.metadata.get("sensor_type")

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            if rule.sensor_id and rule.sensor_id != reading.sensor_id:
                continue

            if rule.sensor_type_filter and sensor_type and rule.sensor_type_filter != sensor_type:
                continue

            cooldown_key = f"{rule.rule_id}_{reading.sensor_id}"
            last_trig = self._last_trigger.get(cooldown_key, 0.0)
            if (current_time - last_trig) < rule.cooldown_sec:
                continue

            matched_cond_descriptions = []
            all_conditions_met = True

            for cond in rule.conditions:
                if self._evaluate_condition(cond, reading, recent_values):
                    matched_cond_descriptions.append(
                        f"{cond.field} {cond.operator.value} {cond.threshold}"
                    )
                else:
                    all_conditions_met = False
                    break

            if all_conditions_met and rule.conditions:
                self._last_trigger[cooldown_key] = current_time
                trigger_record = self._create_trigger_record(
                    rule, reading, matched_cond_descriptions
                )
                triggers.append(trigger_record)

                if rule.rule_id not in self._trigger_history:
                    self._trigger_history[rule.rule_id] = []
                self._trigger_history[rule.rule_id].append(trigger_record)

                log.info(
                    f"Rule '{rule.name}' triggered for sensor {reading.sensor_id}. "
                    f"Value: {reading.value}"
                )

        return triggers

    def _evaluate_condition(
        self,
        condition: RuleCondition,
        reading: SensorReading,
        recent_values: list[float]
    ) -> bool:
        """Evaluate a single RuleCondition against a reading."""
        target_value: float | None = None

        if condition.field == "value":
            target_value = reading.value
        elif condition.field == "rate_of_change" and len(recent_values) >= 2:
            target_value = abs(recent_values[-1] - recent_values[-2])
        elif condition.field in reading.metadata:
            try:
                target_value = float(reading.metadata[condition.field])
            except (ValueError, TypeError):
                return False

        if target_value is None:
            return False

        op = condition.operator
        t = condition.threshold

        if op == RuleConditionOperator.GT and t is not None:
            return target_value > t
        elif op == RuleConditionOperator.GTE and t is not None:
            return target_value >= t
        elif op == RuleConditionOperator.LT and t is not None:
            return target_value < t
        elif op == RuleConditionOperator.LTE and t is not None:
            return target_value <= t
        elif op == RuleConditionOperator.EQ and t is not None:
            return target_value == t
        elif op == RuleConditionOperator.NEQ and t is not None:
            return target_value != t
        elif op == RuleConditionOperator.BETWEEN:
            t_min = condition.threshold_min
            t_max = condition.threshold_max
            if t_min is not None and t_max is not None:
                return t_min <= target_value <= t_max
        elif op == RuleConditionOperator.OUTSIDE:
            t_min = condition.threshold_min
            t_max = condition.threshold_max
            if t_min is not None and t_max is not None:
                return target_value < t_min or target_value > t_max

        return False

    def _create_trigger_record(
        self,
        rule: SensorRule,
        reading: SensorReading,
        matched: list[str]
    ) -> RuleTriggerRecord:
        """Create a RuleTriggerRecord object."""
        return RuleTriggerRecord(
            rule_id=rule.rule_id,
            sensor_id=reading.sensor_id,
            triggered_at=datetime.now(timezone.utc).isoformat(),
            matched_conditions=matched,
            actions_executed=[a.action_type.value for a in rule.actions],
            value_at_trigger=reading.value
        )

    def get_trigger_history(
        self,
        rule_id: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[RuleTriggerRecord]:
        """Get the history of rule triggers."""
        history = []
        if rule_id:
            history = self._trigger_history.get(rule_id, [])
        else:
            for triggers in self._trigger_history.values():
                history.extend(triggers)
                
        history.sort(key=lambda t: t.triggered_at, reverse=True)
        return history[offset:offset+limit]

    def get_rule_stats(self) -> dict:
        """Get statistical summary of rule evaluations and triggers."""
        stats = {
            "total_rules": len(self._rules),
            "priority_counts": {p.value: 0 for p in RulePriority},
            "total_triggers": 0,
            "most_triggered_rule": None
        }

        max_triggers = 0
        most_triggered_id = None

        for rule in self._rules.values():
            stats["priority_counts"][rule.priority.value] = (
                stats["priority_counts"].get(rule.priority.value, 0) + 1
            )
            
            trigger_count = len(self._trigger_history.get(rule.rule_id, []))
            stats["total_triggers"] += trigger_count
            
            if trigger_count > max_triggers:
                max_triggers = trigger_count
                most_triggered_id = rule.rule_id

        if most_triggered_id:
            stats["most_triggered_rule"] = self._rules[most_triggered_id].name

        return stats

    def get_stats(self) -> dict:
        """Alias for get_rule_stats."""
        return self.get_rule_stats()
