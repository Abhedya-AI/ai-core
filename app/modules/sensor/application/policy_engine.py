import time
from uuid import uuid4
from typing import List, Dict
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, ThresholdPolicy, ThresholdPolicyType, AnomalyType, AnomalySeverity
from app.core.logging import get_logger

log = get_logger("app.modules.sensor.application.policy_engine")

class ThresholdPolicyEngine:
    """Engine to evaluate sensor readings against threshold policies."""

    def __init__(self):
        """Initialize with empty policy registry and cooldown tracker."""
        self._policies: Dict[str, List[ThresholdPolicy]] = {}
        self._last_alert_time: Dict[str, float] = {}

    def register_policy(self, policy: ThresholdPolicy) -> None:
        """
        Register a threshold policy.
        
        Args:
            policy: The threshold policy to register.
        """
        if policy.sensor_id not in self._policies:
            self._policies[policy.sensor_id] = []
        
        # Replace if exists
        self._policies[policy.sensor_id] = [p for p in self._policies[policy.sensor_id] if p.id != policy.id]
        self._policies[policy.sensor_id].append(policy)
        log.info(f"Registered policy {policy.id} for sensor {policy.sensor_id}")

    def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy by ID.
        
        Args:
            policy_id: The ID of the policy to remove.
            
        Returns:
            bool: True if policy was removed, False otherwise.
        """
        for sensor_id, policies in self._policies.items():
            initial_count = len(policies)
            self._policies[sensor_id] = [p for p in policies if p.id != policy_id]
            if len(self._policies[sensor_id]) < initial_count:
                log.info(f"Removed policy {policy_id}")
                return True
        return False

    def get_policies(self, sensor_id: str) -> List[ThresholdPolicy]:
        """
        Get all policies for a sensor.
        
        Args:
            sensor_id: The ID of the sensor.
            
        Returns:
            list[ThresholdPolicy]: List of policies for the sensor.
        """
        return self._policies.get(sensor_id, [])

    def evaluate(self, reading: SensorReading, recent_values: List[float]) -> List[SensorAnomaly]:
        """
        Evaluate all applicable policies against a reading.
        
        Args:
            reading: The current sensor reading.
            recent_values: List of recent values for dynamic and rate policies.
            
        Returns:
            list[SensorAnomaly]: List of generated anomalies.
        """
        anomalies = []
        policies = self.get_policies(reading.sensor_id)
        current_time = time.time()

        for policy in policies:
            alert_key = f"{reading.sensor_id}_{policy.id}"
            last_alert = self._last_alert_time.get(alert_key, 0.0)
            
            # Check cooldown
            if current_time - last_alert < policy.cooldown_sec:
                continue

            is_anomalous = False
            details = {}
            
            if policy.policy_type == ThresholdPolicyType.STATIC:
                if policy.min_value is not None and reading.value < policy.min_value:
                    is_anomalous = True
                    details = {"reason": "Below min_value", "threshold": policy.min_value, "value": reading.value}
                elif policy.max_value is not None and reading.value > policy.max_value:
                    is_anomalous = True
                    details = {"reason": "Above max_value", "threshold": policy.max_value, "value": reading.value}
                    
            elif policy.policy_type == ThresholdPolicyType.DYNAMIC:
                if recent_values:
                    sorted_vals = sorted(recent_values)
                    p_low = sorted_vals[int(len(sorted_vals) * 0.05)]
                    p_high = sorted_vals[int(len(sorted_vals) * 0.95)]
                    
                    if reading.value < p_low:
                        is_anomalous = True
                        details = {"reason": "Below dynamic 5th percentile", "threshold": p_low, "value": reading.value}
                    elif reading.value > p_high:
                        is_anomalous = True
                        details = {"reason": "Above dynamic 95th percentile", "threshold": p_high, "value": reading.value}
                        
            elif policy.policy_type == ThresholdPolicyType.RATE:
                if len(recent_values) >= 1:
                    last_value = recent_values[-1]
                    rate_of_change = abs(reading.value - last_value)
                    
                    # Using max_value as rate limit
                    if policy.max_value is not None and rate_of_change > policy.max_value:
                        is_anomalous = True
                        details = {"reason": "Rate of change exceeded limit", "rate": rate_of_change, "limit": policy.max_value}

            if is_anomalous:
                self._last_alert_time[alert_key] = current_time
                anomaly = SensorAnomaly(
                    id=str(uuid4()),
                    sensor_id=reading.sensor_id,
                    timestamp=reading.timestamp,
                    anomaly_type=AnomalyType.THRESHOLD_BREACH,
                    severity=getattr(AnomalySeverity, "HIGH", AnomalySeverity.HIGH),
                    reading_value=reading.value,
                    details=details
                )
                anomalies.append(anomaly)

        return anomalies
