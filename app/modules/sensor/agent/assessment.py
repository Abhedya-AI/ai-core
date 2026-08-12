from app.modules.sensor.domain.models import SensorAnomaly, SensorHealthState, AnomalySeverity, AnomalyType, SensorHealth

class SensorAssessment:
    """Sensor assessment utilities for analyzing anomaly and health data."""
    
    @staticmethod
    def assess(anomalies: list[SensorAnomaly], health_states: list[SensorHealthState]) -> dict:
        """Aggregates multi-engine results into a unified assessment."""
        critical_count = 0
        high_count = 0
        anomaly_types: dict[str, int] = {}
        affected_sensors = set()
        
        # We need a robust way to determine worst severity
        severity_order = {
            AnomalySeverity.INFO: 0,
            AnomalySeverity.LOW: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.HIGH: 3,
            AnomalySeverity.CRITICAL: 4
        }
        
        worst_severity = AnomalySeverity.INFO
        
        for anomaly in anomalies:
            if anomaly.severity == AnomalySeverity.CRITICAL:
                critical_count += 1
            elif anomaly.severity == AnomalySeverity.HIGH:
                high_count += 1
                
            atype = anomaly.type.value if hasattr(anomaly.type, "value") else str(anomaly.type)
            anomaly_types[atype] = anomaly_types.get(atype, 0) + 1
            
            affected_sensors.add(anomaly.sensor_id)
            
            if severity_order.get(anomaly.severity, 0) > severity_order.get(worst_severity, 0):
                worst_severity = anomaly.severity
                
        # Calculate risk multiplier
        risk_multiplier = 1.0
        if anomalies:
            if worst_severity == AnomalySeverity.CRITICAL:
                risk_multiplier = 5.0
            elif worst_severity == AnomalySeverity.HIGH:
                risk_multiplier = 3.0
            elif worst_severity == AnomalySeverity.MEDIUM:
                risk_multiplier = 2.0
            elif worst_severity == AnomalySeverity.LOW:
                risk_multiplier = 1.5
                
        sensors_healthy = 0
        sensors_degraded = 0
        sensors_critical = 0
        sensors_offline = 0
        
        for health in health_states:
            if health.status == SensorHealth.HEALTHY:
                sensors_healthy += 1
            elif health.status == SensorHealth.DEGRADED:
                sensors_degraded += 1
            elif health.status == SensorHealth.CRITICAL:
                sensors_critical += 1
            elif health.status == SensorHealth.OFFLINE:
                sensors_offline += 1
                
        total_sensors = len(health_states)
        fleet_health_pct = (sensors_healthy / total_sensors * 100.0) if total_sensors > 0 else 100.0
        
        return {
            "total_anomalies": len(anomalies),
            "critical_count": critical_count,
            "high_count": high_count,
            "anomaly_types": anomaly_types,
            "affected_sensors": list(affected_sensors),
            "overall_severity": worst_severity.value if hasattr(worst_severity, "value") else str(worst_severity),
            "risk_multiplier": risk_multiplier,
            "sensors_healthy": sensors_healthy,
            "sensors_degraded": sensors_degraded,
            "sensors_critical": sensors_critical,
            "sensors_offline": sensors_offline,
            "fleet_health_pct": fleet_health_pct
        }

    @staticmethod
    def generate_recommendations(anomalies: list[SensorAnomaly], health_states: list[SensorHealthState]) -> list[str]:
        """Generate actionable recommendations based on anomaly patterns."""
        recs = []
        if any(a.severity == AnomalySeverity.CRITICAL for a in anomalies):
            recs.append("Immediate inspection required for sensors reporting CRITICAL anomalies.")
            
        degraded_count = sum(1 for h in health_states if h.status == SensorHealth.DEGRADED)
        if degraded_count > 0:
            recs.append(f"Schedule maintenance for {degraded_count} degraded sensors to prevent critical failure.")
            
        offline_count = sum(1 for h in health_states if h.status == SensorHealth.OFFLINE)
        if offline_count > 0:
            recs.append(f"Investigate {offline_count} offline sensors immediately for potential network or power issues.")
            
        return recs
