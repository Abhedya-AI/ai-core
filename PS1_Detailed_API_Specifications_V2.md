# PS-1 Detailed API Specifications

## API Overview

**Base URL:** `https://api.sentinelai.example.com/api/v1`  
**Authentication:** JWT Bearer Token  
**Default Timeout:** 30 seconds  
**Rate Limit:** 1000 requests/minute  

---

## Authentication Endpoints

### 1. User Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive JWT token

**Request:**
```json
{
  "email": "safety_officer@company.com",
  "password": "SecurePassword123!",
  "remember_me": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "user_id": "usr_12345",
    "email": "safety_officer@company.com",
    "full_name": "John Doe",
    "role": "safety_manager",
    "department": "Safety & Health",
    "avatar_url": "https://cdn.example.com/avatars/john.jpg"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  },
  "preferences": {
    "dashboard_theme": "dark",
    "notification_enabled": true,
    "language": "en"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "INVALID_CREDENTIALS",
  "message": "Email or password is incorrect"
}
```

**Error Codes:**
- `INVALID_CREDENTIALS` - Email/password incorrect
- `USER_DISABLED` - User account disabled
- `USER_NOT_FOUND` - User doesn't exist
- `TOO_MANY_ATTEMPTS` - Account locked (too many login attempts)

---

### 2. Refresh Token

**Endpoint:** `POST /auth/refresh-token`

**Description:** Get new access token using refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

## Risk & Safety Endpoints

### 3. Get Current Risk Status

**Endpoint:** `GET /risk/current`

**Query Parameters:**
```
- zone_id: (optional) Filter by zone
- include_breakdown: (boolean) Include risk factor breakdown
- include_forecast: (boolean) Include 6-hour forecast
```

**Example Request:**
```
GET /risk/current?zone_id=ZONE_A&include_breakdown=true&include_forecast=true
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "timestamp": "2025-06-24T14:30:45Z",
  "current_risk": {
    "overall_score": 62,
    "risk_level": "HIGH",
    "trend": "increasing",
    "trend_direction": "up",
    "last_update": "2025-06-24T14:30:40Z"
  },
  "by_zone": [
    {
      "zone_id": "ZONE_A",
      "zone_name": "Production Area 1",
      "risk_score": 78,
      "risk_level": "CRITICAL",
      "workers_present": 12,
      "equipment_count": 5,
      "active_hazards": ["gas_leak", "high_temperature"],
      "active_permits": ["hot_work_permit_001"]
    },
    {
      "zone_id": "ZONE_B",
      "zone_name": "Production Area 2",
      "risk_score": 45,
      "risk_level": "MEDIUM",
      "workers_present": 8,
      "equipment_count": 3,
      "active_hazards": [],
      "active_permits": []
    }
  ],
  "risk_breakdown": {
    "gas_risk": 0.65,
    "temperature_risk": 0.45,
    "pressure_risk": 0.32,
    "worker_density_risk": 0.55,
    "equipment_health_risk": 0.28,
    "permit_risk": 0.72,
    "maintenance_risk": 0.40
  },
  "forecast": {
    "next_6_hours": [
      {
        "time": "2025-06-24T15:00:00Z",
        "predicted_risk": 65,
        "confidence": 0.89
      },
      {
        "time": "2025-06-24T15:30:00Z",
        "predicted_risk": 68,
        "confidence": 0.87
      },
      {
        "time": "2025-06-24T16:00:00Z",
        "predicted_risk": 72,
        "confidence": 0.85
      },
      {
        "time": "2025-06-24T16:30:00Z",
        "predicted_risk": 75,
        "confidence": 0.82
      },
      {
        "time": "2025-06-24T17:00:00Z",
        "predicted_risk": 78,
        "confidence": 0.80
      },
      {
        "time": "2025-06-24T17:30:00Z",
        "predicted_risk": 80,
        "confidence": 0.78
      }
    ]
  },
  "top_contributing_factors": [
    {
      "factor": "Hot Work Permit Active",
      "weight": 0.25,
      "current_value": "YES",
      "contribution": 0.72
    },
    {
      "factor": "Gas Level",
      "weight": 0.40,
      "current_value": "120 ppm",
      "contribution": 0.65
    },
    {
      "factor": "Worker Count",
      "weight": 0.20,
      "current_value": 12,
      "contribution": 0.55
    }
  ]
}
```

---

### 4. Get Compound Risk Analysis

**Endpoint:** `POST /risk/compound-analysis`

**Description:** Analyze specific compound risk scenario

**Request:**
```json
{
  "zone_id": "ZONE_A",
  "scenario": {
    "gas_level_ppm": 120,
    "temperature_celsius": 45,
    "pressure_bar": 2.5,
    "maintenance_active": true,
    "worker_count": 12,
    "permit_type": "HOT_WORK",
    "permit_active": true,
    "shift_type": "NIGHT",
    "equipment_health": 0.75
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "compound_risk_analysis": {
    "compound_risk_score": 0.89,
    "risk_level": "CRITICAL",
    "requires_emergency_response": true,
    "emergency_trigger_reason": "Multiple critical conditions detected simultaneously",
    "risk_breakdown": {
      "gas_risk_component": {
        "value": 120,
        "normalized_score": 0.85,
        "threshold": 100,
        "status": "EXCEEDS_THRESHOLD"
      },
      "maintenance_risk_component": {
        "active": true,
        "risk_score": 0.60,
        "equipment_affected": ["EQ001", "EQ002"]
      },
      "worker_risk_component": {
        "count": 12,
        "density_score": 0.55,
        "at_risk_count": 8
      },
      "permit_risk_component": {
        "type": "HOT_WORK",
        "status": "ACTIVE",
        "risk_score": 0.72,
        "issued_by": "supervisor_001"
      },
      "shift_risk_component": {
        "shift": "NIGHT",
        "reduced_supervision": true,
        "risk_multiplier": 1.2
      }
    },
    "dangerous_combinations": [
      {
        "condition_1": "High Gas Level (120 ppm)",
        "condition_2": "Hot Work Permit Active",
        "condition_3": "Maintenance Activity",
        "risk_score": 0.95,
        "severity": "CRITICAL",
        "historical_incidents": ["INC-2024-005", "INC-2024-012"],
        "probability_of_incident": 0.78
      },
      {
        "condition_1": "High Temperature (45°C)",
        "condition_2": "High Worker Count (12)",
        "condition_3": "Night Shift",
        "risk_score": 0.72,
        "severity": "HIGH",
        "historical_incidents": ["INC-2024-008"],
        "probability_of_incident": 0.62
      }
    ],
    "recommended_actions": [
      {
        "priority": 1,
        "action": "Stop hot work activities",
        "rationale": "Gas level + hot work permit = explosion risk",
        "estimated_effect": "Reduces risk by 45%"
      },
      {
        "priority": 2,
        "action": "Increase ventilation",
        "rationale": "Lower gas concentration",
        "estimated_effect": "Reduces risk by 30%"
      },
      {
        "priority": 3,
        "action": "Pause maintenance activity",
        "rationale": "Additional hazard during high-risk conditions",
        "estimated_effect": "Reduces risk by 25%"
      },
      {
        "priority": 4,
        "action": "Consider evacuation",
        "rationale": "Risk level exceeds safe operating threshold",
        "estimated_effect": "Eliminates immediate risk"
      }
    ],
    "historical_context": {
      "similar_incidents_count": 5,
      "most_severe_incident": "INC-2024-005",
      "most_severe_outcome": "3 workers hospitalized, plant evacuated",
      "pattern": "Occurs when maintenance + permits overlap + shift changes"
    }
  }
}
```

---

### 5. Get Risk History

**Endpoint:** `GET /risk/history`

**Query Parameters:**
```
- time_range: "1h" | "6h" | "24h" | "7d" | "30d" (default: "24h")
- zone_id: (optional) Filter by zone
- granularity: "1m" | "5m" | "15m" | "1h" (default: auto-selected)
```

**Response (200 OK):**
```json
{
  "success": true,
  "time_range": "24h",
  "granularity": "15m",
  "data": [
    {
      "timestamp": "2025-06-23T14:30:00Z",
      "risk_score": 35,
      "risk_level": "LOW"
    },
    {
      "timestamp": "2025-06-23T14:45:00Z",
      "risk_score": 38,
      "risk_level": "LOW"
    },
    {
      "timestamp": "2025-06-23T15:00:00Z",
      "risk_score": 45,
      "risk_level": "MEDIUM"
    },
    {
      "timestamp": "2025-06-23T15:15:00Z",
      "risk_score": 52,
      "risk_level": "MEDIUM"
    },
    {
      "timestamp": "2025-06-23T15:30:00Z",
      "risk_score": 68,
      "risk_level": "HIGH"
    }
  ],
  "statistics": {
    "average": 48.5,
    "min": 30,
    "max": 82,
    "median": 45,
    "std_dev": 12.3,
    "peak_time": "2025-06-23T22:00:00Z",
    "peak_value": 82
  },
  "zone_breakdown": {
    "ZONE_A": {
      "average": 62,
      "max": 82,
      "incidents": 2
    },
    "ZONE_B": {
      "average": 35,
      "max": 48,
      "incidents": 0
    }
  }
}
```

---

## Sensor Endpoints

### 6. Get Current Sensor Readings

**Endpoint:** `GET /sensors/current`

**Query Parameters:**
```
- sensor_type: (optional) "GAS" | "PRESSURE" | "TEMPERATURE" | "HUMIDITY" | "VIBRATION"
- zone_id: (optional) Filter by zone
- status: (optional) "NORMAL" | "WARNING" | "CRITICAL" | "OFFLINE"
```

**Response (200 OK):**
```json
{
  "success": true,
  "timestamp": "2025-06-24T14:30:45Z",
  "sensors": [
    {
      "sensor_id": "S001",
      "sensor_type": "GAS",
      "location_zone": "ZONE_A",
      "current_reading": {
        "value": 120.5,
        "unit": "ppm",
        "timestamp": "2025-06-24T14:30:40Z",
        "confidence": 0.98
      },
      "status": "CRITICAL",
      "threshold": {
        "warning": 75,
        "critical": 100
      },
      "trend": {
        "direction": "increasing",
        "rate_of_change": 2.3,
        "time_unit": "ppm_per_minute"
      },
      "anomaly_detected": true,
      "anomaly_score": -0.85,
      "anomaly_severity": "HIGH",
      "health": {
        "battery_voltage": 4.2,
        "signal_strength": -45,
        "calibration_status": "valid",
        "last_calibration": "2025-06-01"
      }
    },
    {
      "sensor_id": "S002",
      "sensor_type": "TEMPERATURE",
      "location_zone": "ZONE_A",
      "current_reading": {
        "value": 45.2,
        "unit": "°C",
        "timestamp": "2025-06-24T14:30:42Z",
        "confidence": 0.96
      },
      "status": "WARNING",
      "threshold": {
        "warning": 40,
        "critical": 60
      },
      "trend": {
        "direction": "increasing",
        "rate_of_change": 0.5,
        "time_unit": "°C_per_minute"
      },
      "anomaly_detected": false,
      "anomaly_score": 0.15,
      "health": {
        "battery_voltage": 3.9,
        "signal_strength": -38,
        "calibration_status": "valid",
        "last_calibration": "2025-06-05"
      }
    }
  ],
  "summary": {
    "total_sensors": 2,
    "sensors_normal": 0,
    "sensors_warning": 1,
    "sensors_critical": 1,
    "sensors_offline": 0,
    "anomalies_detected": 1
  }
}
```

---

### 7. Get Sensor Details & History

**Endpoint:** `GET /sensors/{sensor_id}/history`

**Query Parameters:**
```
- time_range: "1h" | "6h" | "24h" | "7d" (default: "24h")
- granularity: "1m" | "5m" | "15m" | "1h" (default: auto)
```

**Response (200 OK):**
```json
{
  "success": true,
  "sensor": {
    "sensor_id": "S001",
    "sensor_type": "GAS",
    "location_zone": "ZONE_A",
    "equipment_id": "EQ001",
    "manufacturer": "Dräger",
    "model": "POLYTRON 8700",
    "installation_date": "2024-01-15",
    "last_calibration": "2025-06-01",
    "next_calibration_due": "2025-09-01",
    "accuracy_rating": 0.99
  },
  "readings": [
    {
      "timestamp": "2025-06-23T14:30:00Z",
      "value": 45.2,
      "status": "NORMAL"
    },
    {
      "timestamp": "2025-06-23T14:45:00Z",
      "value": 52.3,
      "status": "NORMAL"
    },
    {
      "timestamp": "2025-06-23T15:00:00Z",
      "value": 67.8,
      "status": "WARNING"
    },
    {
      "timestamp": "2025-06-23T15:15:00Z",
      "value": 89.2,
      "status": "WARNING"
    },
    {
      "timestamp": "2025-06-23T15:30:00Z",
      "value": 120.5,
      "status": "CRITICAL"
    }
  ],
  "statistics": {
    "average": 75.2,
    "min": 30,
    "max": 120.5,
    "median": 67.8,
    "std_dev": 32.1
  },
  "anomalies_detected": [
    {
      "timestamp": "2025-06-23T15:30:00Z",
      "value": 120.5,
      "anomaly_score": -0.87,
      "severity": "CRITICAL",
      "anomaly_type": "sudden_spike"
    }
  ],
  "forecast": {
    "next_hour_prediction": 125.3,
    "confidence": 0.85,
    "trend": "increasing"
  }
}
```

---

## Alert Endpoints

### 8. Get Active Alerts

**Endpoint:** `GET /alerts/active`

**Query Parameters:**
```
- severity: (optional) "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
- zone_id: (optional) Filter by zone
- include_acknowledged: (boolean) Include acknowledged alerts (default: false)
```

**Response (200 OK):**
```json
{
  "success": true,
  "timestamp": "2025-06-24T14:30:45Z",
  "total_count": 3,
  "alerts": [
    {
      "alert_id": "ALR-2025-001",
      "alert_type": "COMPOUND_RISK",
      "severity": "CRITICAL",
      "title": "Critical Compound Risk Detected in Zone A",
      "description": "Gas level (120 ppm) + Hot Work Permit + Maintenance Active = High explosion risk",
      "created_at": "2025-06-24T14:28:15Z",
      "created_by_agent": "supervisor_agent",
      "affected_zones": ["ZONE_A"],
      "affected_workers": ["W001", "W002", "W003"],
      "affected_equipment": ["EQ001", "EQ002"],
      "impact_assessment": {
        "workers_at_risk": 5,
        "critical_equipment": 2,
        "estimated_impact_radius": "50 meters"
      },
      "recommended_action": "Immediate evacuation of Zone A",
      "action_taken": null,
      "is_acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "status": "OPEN",
      "priority": 1,
      "confidence": 0.94,
      "source_data": {
        "gas_reading": 120,
        "temperature": 45,
        "permit_active": true,
        "worker_count": 5
      }
    },
    {
      "alert_id": "ALR-2025-002",
      "alert_type": "ANOMALY_DETECTED",
      "severity": "HIGH",
      "title": "Gas Sensor Anomaly - Sudden Spike",
      "description": "Gas level spike detected at Zone A sensor S001. Possible sensor malfunction or actual hazard.",
      "created_at": "2025-06-24T14:30:20Z",
      "affected_zones": ["ZONE_A"],
      "recommended_action": "Verify sensor calibration and check for actual gas leak",
      "is_acknowledged": false,
      "status": "OPEN",
      "priority": 2,
      "confidence": 0.89
    },
    {
      "alert_id": "ALR-2025-003",
      "alert_type": "WORKER_IN_RESTRICTED_ZONE",
      "severity": "MEDIUM",
      "title": "Worker Detected in Restricted Zone",
      "description": "Worker W010 detected in Zone B (Restricted - High Gas Risk)",
      "created_at": "2025-06-24T14:29:50Z",
      "affected_zones": ["ZONE_B"],
      "affected_workers": ["W010"],
      "recommended_action": "Notify worker and restrict access",
      "is_acknowledged": false,
      "status": "OPEN",
      "priority": 3
    }
  ],
  "summary": {
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  }
}
```

---

### 9. Acknowledge Alert

**Endpoint:** `POST /alerts/{alert_id}/acknowledge`

**Request:**
```json
{
  "acknowledged_by": "usr_12345",
  "comment": "Investigating the issue. Contacted Zone A supervisor.",
  "action_taken": "Supervisor notified to check equipment",
  "remediation_plan": "Will conduct full safety check within 30 minutes"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "alert_id": "ALR-2025-001",
  "acknowledged_at": "2025-06-24T14:35:20Z",
  "acknowledged_by": "usr_12345",
  "comment": "Investigating the issue. Contacted Zone A supervisor.",
  "status": "ACKNOWLEDGED",
  "message": "Alert acknowledged successfully"
}
```

---

## Permit Endpoints

### 10. Get Active Permits

**Endpoint:** `GET /permits/active`

**Query Parameters:**
```
- zone_id: (optional) Filter by zone
- permit_type: (optional) "HOT_WORK" | "CONFINED_SPACE" | "ELECTRICAL"
- include_expired_soon: (boolean) Include permits expiring in next 1 hour
```

**Response (200 OK):**
```json
{
  "success": true,
  "timestamp": "2025-06-24T14:30:45Z",
  "total_count": 2,
  "permits": [
    {
      "permit_id": "PRM-2025-001",
      "permit_type": "HOT_WORK",
      "issued_by": "sup_001",
      "issued_by_name": "Supervisor John",
      "authorized_workers": [
        {
          "worker_id": "W001",
          "name": "Technician A",
          "role": "Welding Technician"
        },
        {
          "worker_id": "W002",
          "name": "Technician B",
          "role": "Helper"
        }
      ],
      "location_zone": "ZONE_A",
      "equipment_affected": ["EQ001", "EQ002"],
      "start_datetime": "2025-06-24T13:00:00Z",
      "end_datetime": "2025-06-24T17:00:00Z",
      "time_remaining_minutes": 150,
      "status": "ACTIVE",
      "precautions": [
        "All hot work equipment must be inspected before use",
        "Fire watch must be present at all times",
        "Gas sensors must be monitored continuously",
        "No work within 5 meters of flammable materials"
      ],
      "risk_score": 0.72,
      "current_zone_risk": 0.89,
      "compound_risk_warning": true,
      "conflict_with_alerts": ["ALR-2025-001"],
      "permit_conditions_met": {
        "gas_level_acceptable": false,
        "maintenance_not_active": true,
        "fire_watch_present": true,
        "equipment_inspected": true
      },
      "all_conditions_met": false,
      "conditions_not_met": ["Gas level exceeds safe threshold for hot work"]
    },
    {
      "permit_id": "PRM-2025-002",
      "permit_type": "CONFINED_SPACE",
      "issued_by": "sup_002",
      "authorized_workers": [
        {
          "worker_id": "W003",
          "name": "Entry Technician",
          "role": "Confined Space Specialist"
        },
        {
          "worker_id": "W004",
          "name": "Safety Watch",
          "role": "Safety Observer"
        }
      ],
      "location_zone": "ZONE_C",
      "equipment_affected": ["EQ005"],
      "start_datetime": "2025-06-24T10:00:00Z",
      "end_datetime": "2025-06-24T14:00:00Z",
      "time_remaining_minutes": 5,
      "status": "ACTIVE",
      "precautions": [
        "Continuous atmospheric monitoring required",
        "Safety watch must remain outside at all times",
        "Emergency rescue equipment must be on standby",
        "Communication system must be tested before entry"
      ],
      "risk_score": 0.45,
      "compound_risk_warning": false,
      "permit_conditions_met": {
        "atmospheric_monitoring_active": true,
        "safety_watch_present": true,
        "rescue_equipment_ready": true,
        "communication_tested": true
      },
      "all_conditions_met": true
    }
  ]
}
```

---

### 11. Create Permit

**Endpoint:** `POST /permits`

**Request:**
```json
{
  "permit_type": "HOT_WORK",
  "issued_by": "sup_001",
  "location_zone": "ZONE_A",
  "equipment_affected": ["EQ001"],
  "authorized_workers": ["W001", "W002"],
  "start_datetime": "2025-06-24T16:00:00Z",
  "end_datetime": "2025-06-24T18:00:00Z",
  "precautions": [
    "All hot work equipment must be inspected",
    "Fire watch required",
    "Gas sensors must be monitored"
  ],
  "special_conditions": "Requires supervisor approval if gas level > 75 ppm",
  "risk_assessment": {
    "identified_hazards": ["Fire", "Explosion", "Gas exposure"],
    "mitigation_measures": ["Ventilation", "Monitoring", "Fire watch"],
    "estimated_risk_level": "HIGH"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "permit": {
    "permit_id": "PRM-2025-003",
    "permit_type": "HOT_WORK",
    "issued_by": "sup_001",
    "authorized_workers": ["W001", "W002"],
    "location_zone": "ZONE_A",
    "equipment_affected": ["EQ001"],
    "start_datetime": "2025-06-24T16:00:00Z",
    "end_datetime": "2025-06-24T18:00:00Z",
    "status": "PENDING",
    "risk_score": 0.72,
    "pre_approval_checks": {
      "zone_risk_assessment": "YELLOW - Monitor closely",
      "equipment_health_check": "PASS",
      "worker_training_verification": "PASS",
      "resource_availability": "PASS",
      "conflicting_activities": "NONE",
      "weather_conditions": "SUITABLE"
    },
    "approval_required": false,
    "created_at": "2025-06-24T14:35:30Z"
  },
  "message": "Permit created successfully and is ready to be activated"
}
```

---

## Incident Endpoints

### 12. Get Incident History

**Endpoint:** `GET /incidents`

**Query Parameters:**
```
- time_range: "7d" | "30d" | "90d" | "1y" | "all" (default: "30d")
- severity: (optional) "MINOR" | "MAJOR" | "FATAL"
- status: (optional) "OPEN" | "INVESTIGATING" | "RESOLVED" | "CLOSED"
- zone_id: (optional) Filter by zone
- limit: (default: 100, max: 1000)
- offset: (default: 0)
```

**Response (200 OK):**
```json
{
  "success": true,
  "time_range": "30d",
  "pagination": {
    "total": 12,
    "limit": 10,
    "offset": 0,
    "pages": 2
  },
  "incidents": [
    {
      "incident_id": "INC-2025-001",
      "incident_type": "GAS_LEAK",
      "date_time": "2025-06-20T14:30:00Z",
      "location_zone": "ZONE_A",
      "severity": "MAJOR",
      "status": "RESOLVED",
      "description": "Unexpected gas leak detected during maintenance window",
      "workers_involved": ["W001", "W003"],
      "equipment_involved": ["EQ001"],
      "injuries": 0,
      "root_cause": "Valve seal failure due to age and wear",
      "contributing_factors": [
        "Maintenance schedule delayed by 2 weeks",
        "New technician unfamiliar with equipment",
        "Supervisor distracted by concurrent hot work permit"
      ],
      "corrective_actions": [
        "Replace all similar valves in Zone A",
        "Increase maintenance frequency for critical equipment",
        "Enhanced supervisor training on concurrent operations"
      ],
      "regulatory_reported": true,
      "reported_to": ["OISD", "Factory Inspector"],
      "investigation_status": "COMPLETED",
      "investigation_completed_date": "2025-06-22",
      "lessons_learned": "Equipment aging is a critical risk factor. Need predictive maintenance."
    },
    {
      "incident_id": "INC-2025-002",
      "incident_type": "NEAR_MISS",
      "date_time": "2025-06-18T09:15:00Z",
      "location_zone": "ZONE_B",
      "severity": "LOW",
      "status": "CLOSED",
      "description": "Worker nearly fell from platform due to missing handrail",
      "workers_involved": ["W005"],
      "equipment_involved": [],
      "injuries": 0,
      "root_cause": "Maintenance contractor removed handrail and forgot to reinstall",
      "corrective_actions": [
        "Implement checklist for maintenance completion",
        "Increase site inspections for contractor work"
      ],
      "similar_incidents": ["INC-2024-012", "INC-2024-008"],
      "prevention_priority": "HIGH"
    }
  ]
}
```

---

### 13. Create Incident Report

**Endpoint:** `POST /incidents`

**Request:**
```json
{
  "incident_type": "GAS_LEAK",
  "date_time": "2025-06-24T14:30:00Z",
  "location_zone": "ZONE_A",
  "severity": "MAJOR",
  "description": "Sudden gas leak from equipment EQ001",
  "workers_involved": ["W001", "W003"],
  "equipment_involved": ["EQ001"],
  "injuries": {
    "total_count": 1,
    "severe_count": 0,
    "fatalities": 0,
    "injuries_detail": [
      {
        "worker_id": "W001",
        "injury_type": "Chemical burn",
        "severity": "MINOR",
        "hospitalized": false
      }
    ]
  },
  "immediate_actions_taken": [
    "Evacuated Zone A",
    "Shut down EQ001",
    "Activated ventilation",
    "Called emergency services"
  ],
  "preliminary_root_cause": "Equipment malfunction",
  "contributing_factors": [
    "Last maintenance was 6 months ago",
    "Preventive maintenance skipped due to schedule pressure"
  ],
  "witness_statements": [
    {
      "worker_id": "W003",
      "statement": "Heard a hissing sound followed by strong smell. Immediately alerted supervisor."
    }
  ],
  "photos_attached": ["img_001.jpg", "img_002.jpg"],
  "videos_attached": ["vid_001.mp4"],
  "emergency_response_time_minutes": 8
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "incident": {
    "incident_id": "INC-2025-015",
    "incident_type": "GAS_LEAK",
    "date_time": "2025-06-24T14:30:00Z",
    "location_zone": "ZONE_A",
    "severity": "MAJOR",
    "status": "OPEN",
    "created_at": "2025-06-24T14:45:30Z",
    "created_by": "usr_12345",
    "initial_assessment": {
      "immediate_risk_to_others": true,
      "evacuation_required": true,
      "regulatory_notification_required": true
    },
    "next_steps": [
      "Assign incident investigator",
      "Notify regulatory authorities (within 24 hours)",
      "Conduct detailed root cause analysis",
      "Identify and implement corrective actions"
    ]
  }
}
```

---

## Emergency Response Endpoints

### 14. Trigger Emergency Evacuation

**Endpoint:** `POST /emergency/evacuate`

**Request:**
```json
{
  "incident_id": "INC-2025-015",
  "affected_zones": ["ZONE_A"],
  "evacuation_type": "IMMEDIATE",
  "hazard_type": "GAS_LEAK",
  "estimated_workers_affected": 12,
  "emergency_contact_authorized": "usr_12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "emergency_response": {
    "incident_id": "INC-2025-015",
    "emergency_id": "EMG-2025-001",
    "status": "ACTIVE",
    "activated_at": "2025-06-24T14:45:00Z",
    "hazard_type": "GAS_LEAK",
    "severity": "CRITICAL",
    "affected_zones": ["ZONE_A"],
    "evacuation_plan": {
      "primary_route": "Zone A South Exit → Assembly Point Alpha",
      "secondary_route": "Zone A East Stairwell → Assembly Point Beta",
      "estimated_evacuation_time_minutes": 4,
      "assembly_point_primary": {
        "name": "Assembly Point Alpha",
        "coordinates": [20.5945, 78.9629],
        "capacity": 50,
        "distance_from_zone": "150 meters"
      }
    },
    "team_assignments": [
      {
        "team_id": "TEAM_001",
        "team_leader": "sup_001",
        "members": ["W001", "W002", "W003"],
        "assigned_area": "Zone A - North Section",
        "task": "Evacuate workers and conduct headcount",
        "estimated_time_minutes": 3
      },
      {
        "team_id": "FIRE_TEAM_001",
        "team_leader": "fb_001",
        "members": ["fb_001", "fb_002", "fb_003"],
        "assigned_area": "Zone A - Equipment area",
        "task": "Assess hazard and deploy containment",
        "estimated_time_minutes": 5
      }
    ],
    "notifications_sent": {
      "sms_sent_count": 15,
      "email_sent_count": 8,
      "push_notifications_sent_count": 25,
      "sirens_activated": true,
      "alarm_status": "CONTINUOUS"
    },
    "incident_report": {
      "report_id": "RPT-2025-001",
      "preliminary_assessment": "Gas leak in Zone A, immediate evacuation initiated",
      "regulatory_notification_status": "PENDING",
      "expected_notification_time": "2025-06-24T15:00:00Z"
    },
    "next_steps": [
      "Monitor evacuation progress",
      "Establish incident command center",
      "Begin worker accountability checks",
      "Initiate medical assessment if injuries detected",
      "Prepare regulatory notifications"
    ]
  }
}
```

---

## Compliance & Reporting Endpoints

### 15. Get Compliance Status

**Endpoint:** `GET /compliance/status`

**Query Parameters:**
```
- standard: (optional) "OISD" | "FACTORY_ACT" | "DGMS" | "OSHA" | "ALL" (default: "ALL")
- include_gaps: (boolean) Include compliance gaps (default: true)
- include_remediation: (boolean) Include remediation timelines (default: true)
```

**Response (200 OK):**
```json
{
  "success": true,
  "timestamp": "2025-06-24T14:30:45Z",
  "overall_compliance_score": 0.87,
  "compliance_status": {
    "OISD": {
      "standard_name": "Oil Industry Safety Directorate",
      "compliance_score": 0.92,
      "compliance_status": "COMPLIANT",
      "total_requirements": 45,
      "met_requirements": 41,
      "unmet_requirements": 4,
      "critical_gaps": [
        {
          "requirement_id": "OISD-105-003",
          "description": "Permit-to-work system must be computerized",
          "current_status": "MANUAL_SYSTEM",
          "required_by": "2025-12-31",
          "remediation_plan": "Implement SentinelAI permit management module",
          "assigned_to": "IT Team",
          "estimated_completion": "2025-10-15",
          "status": "IN_PROGRESS"
        }
      ]
    },
    "FACTORY_ACT": {
      "standard_name": "Factories Act, 1948",
      "compliance_score": 0.88,
      "compliance_status": "COMPLIANT",
      "total_requirements": 32,
      "met_requirements": 28,
      "unmet_requirements": 4,
      "critical_gaps": []
    },
    "DGMS": {
      "standard_name": "Directorate General of Mine Safety",
      "compliance_score": 0.82,
      "compliance_status": "PARTIALLY_COMPLIANT",
      "total_requirements": 28,
      "met_requirements": 23,
      "unmet_requirements": 5,
      "critical_gaps": []
    }
  },
  "recent_violations": [
    {
      "violation_id": "VIO-2025-001",
      "standard": "OISD-STD-105",
      "description": "Manual permit log detected instead of computerized system",
      "detected_date": "2025-06-20",
      "severity": "MEDIUM",
      "remediation_deadline": "2025-08-20",
      "status": "IN_REMEDIATION"
    }
  ],
  "compliance_trends": {
    "last_30_days": 0.85,
    "last_90_days": 0.82,
    "trend": "improving",
    "projected_score_30_days": 0.89
  }
}
```

---

### 16. Generate Incident Report (PDF/JSON)

**Endpoint:** `GET /incidents/{incident_id}/report`

**Query Parameters:**
```
- format: "PDF" | "JSON" | "HTML" (default: "JSON")
- include_photos: (boolean) Include photos in PDF (default: true)
- include_analysis: (boolean) Include root cause analysis (default: true)
```

**Response (200 OK):**
```json
{
  "success": true,
  "incident_id": "INC-2025-015",
  "report": {
    "report_id": "RPT-2025-001",
    "incident_summary": {
      "type": "Gas Leak",
      "date_time": "2025-06-24T14:30:00Z",
      "location": "Zone A, Equipment EQ001",
      "severity": "MAJOR",
      "workers_affected": 12,
      "injuries": 1,
      "fatalities": 0,
      "emergency_response_time_minutes": 8
    },
    "root_cause_analysis": {
      "immediate_cause": "Valve seal failure due to material degradation",
      "underlying_causes": [
        "Maintenance schedule delay",
        "Aging equipment without replacement plan",
        "Insufficient preventive maintenance frequency"
      ],
      "contributing_factors": [
        "Supervisor distraction due to concurrent permits",
        "New technician unfamiliar with equipment specifics"
      ],
      "root_cause_diagram": "Available in PDF format"
    },
    "corrective_actions": [
      {
        "action_id": "CA-001",
        "action": "Replace all similar valves in Zone A",
        "responsible_party": "Maintenance Manager",
        "target_completion_date": "2025-07-15",
        "status": "IN_PROGRESS",
        "expected_risk_reduction": 0.45
      },
      {
        "action_id": "CA-002",
        "action": "Implement predictive maintenance for equipment EQ001-EQ010",
        "responsible_party": "Engineering Team",
        "target_completion_date": "2025-08-30",
        "status": "PLANNED",
        "expected_risk_reduction": 0.35
      }
    ],
    "similar_incidents": [
      {
        "incident_id": "INC-2024-005",
        "date": "2025-01-12",
        "type": "Valve seal failure",
        "outcome": "No injuries",
        "actions_taken": "Replaced valve but no preventive maintenance program implemented"
      }
    ],
    "preventive_measures": [
      "Increase valve inspection frequency from annual to quarterly",
      "Implement seal material upgrade program",
      "Enhanced training for technicians on equipment aging",
      "Concurrent permit conflict detection system"
    ],
    "regulatory_compliance": {
      "OISD_compliance": "COMPLIANT",
      "reporting_status": "REPORTED",
      "reported_date": "2025-06-24T15:30:00Z",
      "reported_to": ["DGFASLI", "State Labor Department"]
    },
    "signatures": {
      "prepared_by": "Safety Officer - John Doe",
      "reviewed_by": "Safety Manager - Jane Smith",
      "approved_by": "Plant Manager - Robert Wilson"
    }
  },
  "report_url": "https://api.example.com/reports/RPT-2025-001.pdf",
  "download_expires_in_days": 30
}
```

---

## WebSocket Events (Real-Time Updates)

**WebSocket URL:** `wss://api.sentinelai.example.com/ws/dashboard`

**Subscribe to Channel:**
```json
{
  "action": "subscribe",
  "channels": ["risk-updates", "alert-events", "incident-events"]
}
```

**Example Event - Risk Score Updated:**
```json
{
  "event_type": "risk_score_updated",
  "timestamp": "2025-06-24T14:31:00Z",
  "data": {
    "zone_id": "ZONE_A",
    "previous_score": 62,
    "current_score": 75,
    "risk_level": "HIGH",
    "change_reason": "Gas level increased from 100 ppm to 125 ppm"
  }
}
```

**Example Event - New Alert:**
```json
{
  "event_type": "alert_created",
  "timestamp": "2025-06-24T14:31:15Z",
  "data": {
    "alert_id": "ALR-2025-004",
    "alert_type": "CRITICAL_RISK",
    "severity": "CRITICAL",
    "zone": "ZONE_A",
    "message": "Compound risk detected - immediate action required"
  }
}
```

---

## Error Response Format

**All endpoints may return errors in this format:**

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "error_message",
    "validation_errors": []
  },
  "request_id": "req_12345",
  "timestamp": "2025-06-24T14:30:45Z"
}
```

**Common Error Codes:**
- `INVALID_REQUEST` - Malformed request
- `AUTHENTICATION_FAILED` - Invalid token
- `AUTHORIZATION_DENIED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Resource doesn't exist
- `DUPLICATE_RESOURCE` - Resource already exists
- `VALIDATION_ERROR` - Input validation failed
- `INTERNAL_SERVER_ERROR` - Server error
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

**API Version:** 1.0  
**Last Updated:** June 2025  
**Documentation Status:** Complete



---

# ARCHITECTURE V2 API ADDITIONS

## 17. Root Cause Analysis API

### Analyze Root Cause

**Endpoint:** `POST /analysis/root-cause`

**Description:** Perform AI-assisted root cause analysis using incidents, sensor history, permits, maintenance records, and graph relationships.

**Request**
```json
{
  "incident_id": "INC-2025-015",
  "include_similar_incidents": true,
  "include_graph_analysis": true
}
```

**Response**
```json
{
  "success": true,
  "root_cause_analysis": {
    "primary_cause": {
      "cause": "Valve Failure",
      "probability": 0.65
    },
    "secondary_causes": [
      {
        "cause": "Maintenance Delay",
        "probability": 0.22
      },
      {
        "cause": "Human Error",
        "probability": 0.13
      }
    ],
    "recommended_actions": [
      "Replace valve assembly",
      "Increase inspection frequency"
    ]
  }
}
```

---

## 18. Explainable AI API

### Explain Risk Score

**Endpoint:** `GET /risk/explain/{zone_id}`

**Description:** Returns SHAP-style feature contributions for risk predictions.

**Response**
```json
{
  "success": true,
  "zone_id": "ZONE_A",
  "risk_score": 92,
  "feature_contributions": [
    {
      "feature": "Gas Level",
      "importance": 42
    },
    {
      "feature": "Permit Risk",
      "importance": 28
    },
    {
      "feature": "Worker Density",
      "importance": 18
    }
  ],
  "explanation": "High gas levels combined with active permit activity significantly increased risk."
}
```

---

## 19. Simulation & What-If API

### Run Simulation

**Endpoint:** `POST /simulation/what-if`

**Description:** Simulate future risk under hypothetical conditions.

**Request**
```json
{
  "zone_id": "ZONE_A",
  "scenario": {
    "gas_level": 140,
    "worker_count": 15,
    "permit_active": true,
    "maintenance_active": true
  }
}
```

**Response**
```json
{
  "success": true,
  "predicted_risk": 97,
  "incident_probability": 0.81,
  "recommended_action": "Immediate shutdown and evacuation"
}
```

---

## 20. GraphRAG API

### Query GraphRAG

**Endpoint:** `POST /graphrag/query`

**Description:** Query the GraphRAG system using regulations, incidents, graph traversal, and vector retrieval.

**Request**
```json
{
  "question": "Why is Zone A currently dangerous?"
}
```

**Response**
```json
{
  "success": true,
  "answer": "Zone A has elevated gas concentration, an active hot work permit, and recent maintenance activity.",
  "citations": [
    "OISD-STD-105",
    "Incident INC-2024-005"
  ],
  "graph_entities": [
    "ZONE_A",
    "HOT_WORK_PERMIT",
    "EQ001"
  ]
}
```

---

## 21. Hazard Propagation API

### Predict Hazard Spread

**Endpoint:** `POST /hazard/propagate`

**Description:** Simulate hazard spread through equipment, workers, and adjacent zones.

**Request**
```json
{
  "hazard_type": "GAS_LEAK",
  "origin_zone": "ZONE_A"
}
```

**Response**
```json
{
  "success": true,
  "affected_zones": [
    "ZONE_A",
    "ZONE_B"
  ],
  "affected_workers": [
    "W001",
    "W002",
    "W010"
  ],
  "impact_radius_meters": 75,
  "time_to_critical_minutes": 15,
  "recommended_action": "Evacuate Zone A and restrict access to Zone B"
}
```
