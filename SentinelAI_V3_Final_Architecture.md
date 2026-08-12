
# SENTINELAI V3 - ARCHITECT REVIEWED EDITION

## IMPORTANT ARCHITECTURAL REVISIONS APPLIED

This V3 version supersedes the original architecture in the following areas:

### Core AI Differentiators
- GraphRAG++ replaces standard RAG
- Root Cause Analysis Agent added
- Simulation / What-If Agent added
- Explainable AI Layer (SHAP) added
- Compound Risk Intelligence promoted to standalone service
- Hazard Propagation Engine added
- Neo4j Graph Data Science added
- Industrial Memory Layer added

### Hackathon Optimization
Removed as non-essential:
- Kubernetes
- ELK Stack
- Jaeger
- Prometheus
- gRPC
- MongoDB

Recommended Final Stack:
- FastAPI
- PostgreSQL
- Neo4j
- FAISS
- Kafka
- YOLO
- XGBoost
- LSTM/TFT
- LangGraph

## UPDATED MULTI-AGENT ARCHITECTURE

Supervisor Agent
├── Vision Agent
├── Sensor Agent
├── Risk Agent
├── Forecast Agent
├── Compliance Agent
├── Incident Agent
├── Root Cause Agent
├── Simulation Agent
├── Emergency Agent
└── Recommendation Agent

## UPDATED AI SERVICES

AI Layer
├── Vision Intelligence Service
├── Sensor Intelligence Service
├── Risk Prediction Service
├── Compound Risk Intelligence Service
├── Forecast Intelligence Service
├── Graph Intelligence Service
├── GraphRAG++ Service
├── Root Cause Analysis Service
├── Explainability Service
├── Simulation Intelligence Service
├── Hazard Propagation Engine
└── Emergency Intelligence Service

## UPDATED GRAPHRAG PIPELINE

User Query
→ Entity Extraction
→ Neo4j Traversal
→ Incident Expansion
→ Regulation Expansion
→ Hybrid Retrieval
→ Cross Encoder Reranking
→ LLM Generation
→ Evidence + Citations

## UPDATED DASHBOARD MODULES

1. Executive Command Center
2. AI Command Center
3. Compound Risk Center
4. Explainability Center
5. Graph Intelligence Center
6. Simulation Center
7. Emergency Center
8. Digital Twin Center
9. Compliance Center
10. Root Cause Center

## UPDATED KNOWLEDGE GRAPH

Graph Data Science Algorithms:
- PageRank
- Community Detection
- Node Similarity
- Betweenness Centrality
- Shortest Path

## UPDATED CORE JUDGING STORY

Observe
→ Reason
→ Predict
→ Explain
→ Simulate
→ Act



--- ORIGINAL SCHEMA BELOW ---

# PS-1: AI-Powered Industrial Safety Intelligence
## Complete System Architecture & Implementation Schema

---

## EXECUTIVE OVERVIEW

**Project Name:** SentinelAI - Industrial Safety Intelligence Platform
**Complexity Level:** Enterprise-Grade Industrial Operating System
**Timeline:** 4-Week Development Sprint
**Team Size:** 8-12 members (distributed across roles)
**Core Objective:** Transform reactive safety monitoring into predictive safety intelligence

**Key Differentiator:** Not a dashboard. A decision intelligence system that observes, reasons, predicts, explains, and acts autonomously.

---

## TABLE OF CONTENTS

1. [System Architecture Overview](#system-architecture-overview)
2. [Data Layer Specification](#data-layer-specification)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [AI/ML Models & Algorithms](#aiml-models--algorithms)
6. [Multi-Agent System Design](#multi-agent-system-design)
7. [Database & Storage Schemas](#database--storage-schemas)
8. [API Specifications](#api-specifications)
9. [Frontend-Backend Integration](#frontend-backend-integration)
10. [Technology Stack](#technology-stack)
11. [Feature Specifications](#feature-specifications)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Deployment Architecture](#deployment-architecture)

---

## SYSTEM ARCHITECTURE OVERVIEW

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SENTINELAI ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────┘

PHYSICAL LAYER (Real-Time Data Sources)
├── IoT Sensors (Gas, Pressure, Temp, Humidity, Vibration)
├── SCADA Systems
├── CCTV Feeds (Real-time video streams)
├── Permit Logs
├── Maintenance Records
├── Worker Presence Systems (RFID/GPS)
└── Historical Incident Reports

        ↓ [Edge Processing + Data Collection]

DATA INGESTION LAYER
├── Message Queue (Kafka/RabbitMQ)
├── Stream Processors (Kafka Streams/Spark Streaming)
├── Data Validation & Normalization
└── Time-Series Database (InfluxDB/TimescaleDB)

        ↓ [Real-time & Batch Processing]

BACKEND SERVICES LAYER
├── Vision Intelligence Service
├── Sensor Intelligence Service
├── Risk Prediction Service
├── Knowledge Graph Service
├── Compliance Intelligence Service
├── Emergency Response Service
├── Multi-Agent Orchestrator
└── API Gateway

        ↓ [WebSocket/REST/gRPC]

FRONTEND LAYER
├── Web Dashboard (React/Vue)
├── Mobile App (React Native/Flutter)
├── Command Center Interface
├── Mobile Field App
└── Public Advisory Portal

        ↓ [User Interactions & Commands]

DECISION OUTPUT
├── Automated Alerts
├── Evacuation Routes
├── Team Assignments
├── Regulatory Reports
└── Dashboard Visualizations
```

---

## DATA LAYER SPECIFICATION

### 1. Data Sources & Ingestion

#### IoT Sensor Data
```json
{
  "sensor_data_schema": {
    "sensor_id": "string (unique identifier)",
    "sensor_type": "enum [GAS, PRESSURE, TEMPERATURE, HUMIDITY, VIBRATION]",
    "location_zone": "string (Zone A, B, C, etc)",
    "value": "float",
    "unit": "string (ppm, bar, °C, %, m/s²)",
    "timestamp": "ISO8601",
    "status": "enum [NORMAL, WARNING, CRITICAL, OFFLINE]",
    "confidence": "float (0-100)",
    "metadata": {
      "equipment_id": "string",
      "sensor_model": "string",
      "calibration_date": "date",
      "accuracy_rating": "float"
    }
  },
  "expected_frequency": "1-10 Hz per sensor",
  "daily_data_volume": "~50-100 GB (500 sensors × 24 hours)",
  "retention_policy": "1 year hot storage, 5 years archive"
}
```

#### SCADA System Data
```json
{
  "scada_data_schema": {
    "equipment_id": "string",
    "equipment_type": "string (Boiler, Pump, Valve, etc)",
    "operating_parameters": {
      "run_status": "enum [RUNNING, STOPPED, IDLE, ERROR]",
      "power_consumption": "float (kW)",
      "efficiency_percentage": "float",
      "maintenance_hours": "integer",
      "last_maintenance": "timestamp"
    },
    "anomaly_indicators": {
      "vibration_level": "float",
      "temperature_deviation": "float",
      "pressure_spike": "boolean"
    },
    "timestamp": "ISO8601",
    "health_score": "float (0-100)"
  }
}
```

#### CCTV Feed Data
```json
{
  "video_stream_schema": {
    "camera_id": "string",
    "location_zone": "string",
    "stream_url": "rtsp://",
    "resolution": "1080p|4K",
    "fps": "integer (25-30)",
    "encoding": "H264|H265",
    "processing_status": "enum [ACTIVE, INACTIVE, ERROR]",
    "storage_location": "s3://bucket/camera_id/",
    "retention": "7 days hot, 30 days archive"
  },
  "processed_frame_schema": {
    "frame_id": "string",
    "timestamp": "ISO8601",
    "detections": [
      {
        "detection_id": "string",
        "class": "string (HELMET, VEST, WORKER, FIRE, SMOKE, FALL, etc)",
        "confidence": "float (0-100)",
        "bbox": "[x1, y1, x2, y2]",
        "zone": "string",
        "worker_id": "string (if tracked)"
      }
    ]
  }
}
```

#### Permit System Data
```json
{
  "permit_schema": {
    "permit_id": "string (unique)",
    "permit_type": "enum [HOT_WORK, CONFINED_SPACE, ELECTRICAL, EXCAVATION, LOCK_TAGOUT]",
    "issued_by": "string (supervisor name)",
    "authorized_workers": ["worker_id_1", "worker_id_2"],
    "location": "string (Zone identifier)",
    "equipment_affected": ["equipment_id_1"],
    "start_time": "ISO8601",
    "end_time": "ISO8601",
    "precautions": ["precaution_1", "precaution_2"],
    "status": "enum [PENDING, ACTIVE, EXPIRED, CANCELLED, COMPLETED]",
    "associated_risks": [
      {
        "risk_type": "string",
        "mitigation": "string"
      }
    ]
  },
  "expected_frequency": "10-20 new permits per shift"
}
```

#### Maintenance Records
```json
{
  "maintenance_schema": {
    "maintenance_id": "string",
    "equipment_id": "string",
    "maintenance_type": "enum [PREVENTIVE, CORRECTIVE, INSPECTION]",
    "scheduled_start": "ISO8601",
    "actual_start": "ISO8601",
    "actual_end": "ISO8601",
    "assigned_technician": "string",
    "work_description": "string",
    "parts_replaced": [
      {
        "part_id": "string",
        "part_name": "string",
        "replacement_date": "ISO8601"
      }
    ],
    "issues_found": ["issue_1", "issue_2"],
    "next_maintenance_due": "ISO8601",
    "status": "enum [SCHEDULED, IN_PROGRESS, COMPLETED, DEFERRED]"
  }
}
```

#### Worker/Shift Data
```json
{
  "shift_schema": {
    "shift_id": "string",
    "shift_number": "enum [SHIFT_1, SHIFT_2, SHIFT_3]",
    "start_time": "ISO8601",
    "end_time": "ISO8601",
    "supervisor": "string",
    "assigned_workers": [
      {
        "worker_id": "string",
        "name": "string",
        "role": "string (Technician, Operator, etc)",
        "zone_assigned": "string",
        "training_level": "enum [JUNIOR, INTERMEDIATE, SENIOR]"
      }
    ],
    "handover_notes": "string",
    "incidents_reported": "integer"
  },
  "worker_location_schema": {
    "worker_id": "string",
    "timestamp": "ISO8601",
    "current_zone": "string",
    "gps_coordinates": "[latitude, longitude]",
    "device_id": "string (RFID/mobile tag)"
  }
}
```

#### Incident & Near-Miss Reports
```json
{
  "incident_schema": {
    "incident_id": "string",
    "incident_type": "enum [FATALITY, MAJOR_INJURY, MINOR_INJURY, NEAR_MISS, PROPERTY_DAMAGE]",
    "date_time": "ISO8601",
    "location": "string",
    "workers_involved": ["worker_id_1"],
    "equipment_involved": ["equipment_id_1"],
    "root_cause": "string",
    "contributing_factors": ["factor_1", "factor_2"],
    "description": "string",
    "corrective_actions": ["action_1", "action_2"],
    "regulatory_references": ["OISD-105", "Factory Act Section 25"],
    "severity_score": "integer (1-10)",
    "prevention_priority": "enum [CRITICAL, HIGH, MEDIUM, LOW]"
  }
}
```

---

## BACKEND ARCHITECTURE

### Backend Technology Stack
- **Runtime:** Python 3.11+ (FastAPI) + Node.js (Express) for microservices
- **Async Processing:** Celery + Redis
- **Message Queue:** Apache Kafka for event streaming
- **Graph Database:** Neo4j for knowledge graphs
- **Databases:** PostgreSQL (structured), InfluxDB (time-series), MongoDB (documents)
- **Cache:** Redis
- **ML Serving:** FastAPI + ONNX Runtime, TensorFlow Serving
- **Container:** Docker + Kubernetes
- **API:** FastAPI, gRPC for inter-service communication

### Backend Microservices Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES LAYER                             │
└──────────────────────────────────────────────────────────────────────┘

1. API GATEWAY (FastAPI + Kong)
   ├── Authentication/Authorization (JWT)
   ├── Rate Limiting
   ├── Request Routing
   └── Response Aggregation

2. DATA INGESTION SERVICE
   ├── Sensor Data Collector
   ├── SCADA Connector
   ├── CCTV Stream Ingester
   ├── File Upload Handler
   └── Data Normalization Pipeline

3. STREAM PROCESSING SERVICE (Kafka Streams)
   ├── Real-time Aggregation
   ├── Window-based Analytics
   ├── Stream Joins
   └── Anomaly Detection Streaming

4. VISION INTELLIGENCE SERVICE
   ├── YOLO Model Server
   ├── Frame Processing Pipeline
   ├── Object Tracking
   ├── PPE Detection
   ├── Fall Detection
   └── Crowd Analysis

5. SENSOR INTELLIGENCE SERVICE
   ├── Anomaly Detection Engine
   ├── Time-Series Analysis
   ├── Pattern Recognition
   └── Alert Generation

6. RISK PREDICTION SERVICE
   ├── XGBoost Model Server
   ├── LightGBM Model Server
   ├── Random Forest Ensemble
   ├── Feature Engineering Pipeline
   └── Risk Scoring Engine

7. FORECAST SERVICE (LSTM/Transformer)
   ├── Time-Series Forecasting
   ├── Trend Analysis
   ├── Anomaly Prediction
   └── Confidence Intervals

8. KNOWLEDGE GRAPH SERVICE
   ├── Neo4j Driver
   ├── Graph Query Engine
   ├── Entity Management
   ├── Relationship Mapping
   └── Inference Engine

9. COMPLIANCE & RAG SERVICE
   ├── Document Indexing (FAISS/Pinecone)
   ├── RAG Pipeline (BM25 + Dense Retrieval)
   ├── Regulation Matcher
   ├── Compliance Scorer
   └── LLM Integration (Claude/GPT)

10. MULTI-AGENT ORCHESTRATOR
    ├── Vision Agent
    ├── Sensor Agent
    ├── Risk Agent
    ├── Forecast Agent
    ├── Compliance Agent
    ├── Incident Agent
    ├── Emergency Agent
    └── Supervisor Agent

11. EMERGENCY RESPONSE SERVICE
    ├── Evacuation Route Calculator
    ├── Team Assignment Engine
    ├── Notification Service
    ├── Incident Report Generator
    └── Regulatory Document Generator

12. GEOSPATIAL SERVICE
    ├── Plant Map Manager
    ├── Zone Management
    ├── Heatmap Generator
    ├── Route Optimization
    └── Visualization Engine

13. NOTIFICATION SERVICE
    ├── Email Handler
    ├── SMS Handler
    ├── Push Notification
    ├── Siren/Alarm Integration
    └── Mobile App Alerts

14. AUTHENTICATION & AUTHORIZATION
    ├── JWT Token Manager
    ├── Role-Based Access Control
    ├── Audit Logging
    └── Multi-factor Authentication

15. LOGGING & MONITORING
    ├── ELK Stack (Elasticsearch, Logstash, Kibana)
    ├── Prometheus Metrics
    ├── Grafana Dashboards
    ├── Distributed Tracing (Jaeger)
    └── Alert Manager
```

### Backend Service Specifications

#### 1. API Gateway Service
```python
# FastAPI API Gateway
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional
import jwt

app = FastAPI(title="SentinelAI API Gateway")

class AuthHandler:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest) -> LoginResponse:
    # Authenticate user
    # Generate JWT token
    pass

@app.post("/api/v1/sensor/data")
async def ingest_sensor_data(data: SensorData, token: str = Depends(HTTPBearer())):
    # Route to Data Ingestion Service
    pass

@app.get("/api/v1/risk/current")
async def get_current_risk(zone: str = None, token: str = Depends(HTTPBearer())):
    # Call Risk Prediction Service
    pass

@app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview(token: str = Depends(HTTPBearer())):
    # Aggregate data from multiple services
    pass
```

#### 2. Data Ingestion Service
```python
from kafka import KafkaProducer
from typing import Dict, Any
import json
from datetime import datetime

class DataIngestionService:
    def __init__(self, kafka_bootstrap: str):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    # Sensor Data Ingestion
    async def ingest_sensor_data(self, sensor_data: Dict[str, Any]) -> str:
        """
        Validate and ingest sensor data to Kafka
        """
        # Validate schema
        validated_data = self.validate_sensor_schema(sensor_data)
        
        # Add timestamp if missing
        validated_data['received_at'] = datetime.utcnow().isoformat()
        
        # Publish to Kafka topic
        self.producer.send('sensor-events', value=validated_data)
        
        return validated_data['sensor_id']
    
    # SCADA Data Ingestion
    async def ingest_scada_data(self, scada_data: Dict[str, Any]) -> str:
        validated_data = self.validate_scada_schema(scada_data)
        self.producer.send('scada-events', value=validated_data)
        return validated_data['equipment_id']
    
    # Permit Data Ingestion
    async def ingest_permit_data(self, permit_data: Dict[str, Any]) -> str:
        validated_data = self.validate_permit_schema(permit_data)
        self.producer.send('permit-events', value=validated_data)
        return validated_data['permit_id']
    
    # CCTV Frame Ingestion (from Edge Processing)
    async def ingest_cctv_frame(self, frame_data: Dict[str, Any]) -> str:
        validated_data = self.validate_cctv_schema(frame_data)
        self.producer.send('cctv-events', value=validated_data)
        return validated_data['frame_id']
    
    def validate_sensor_schema(self, data: Dict) -> Dict:
        # Schema validation logic
        required_fields = ['sensor_id', 'sensor_type', 'value', 'timestamp']
        if not all(field in data for field in required_fields):
            raise ValueError("Missing required fields")
        return data
```

#### 3. Stream Processing Service (Kafka Streams)
```python
from kafka import KafkaConsumer, KafkaProducer
from collections import defaultdict
from datetime import datetime, timedelta
import json

class StreamProcessor:
    def __init__(self, kafka_bootstrap: str):
        self.consumer = KafkaConsumer(
            'sensor-events', 'scada-events', 'permit-events',
            bootstrap_servers=kafka_bootstrap,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Time window for aggregation
        self.sensor_window = defaultdict(list)  # {sensor_id: [readings]}
        self.window_duration = timedelta(minutes=5)
    
    def run(self):
        """Main stream processing loop"""
        for message in self.consumer:
            event = message.value
            
            if message.topic == 'sensor-events':
                self.process_sensor_event(event)
            elif message.topic == 'scada-events':
                self.process_scada_event(event)
            elif message.topic == 'permit-events':
                self.process_permit_event(event)
    
    def process_sensor_event(self, event: Dict):
        """
        Aggregate sensor data and detect anomalies
        """
        sensor_id = event['sensor_id']
        
        # Add to window
        self.sensor_window[sensor_id].append(event)
        
        # Calculate aggregates every N events
        if len(self.sensor_window[sensor_id]) % 10 == 0:
            aggregated = self.aggregate_readings(
                self.sensor_window[sensor_id][-60:]  # Last 60 readings
            )
            
            # Send aggregated data
            self.producer.send('sensor-aggregated', value=aggregated)
            
            # Check for anomalies
            if self.detect_anomaly(aggregated):
                self.producer.send('anomaly-alerts', value={
                    'sensor_id': sensor_id,
                    'anomaly_type': 'trend_deviation',
                    'severity': 'high',
                    'timestamp': event['timestamp']
                })
    
    def aggregate_readings(self, readings: list) -> Dict:
        """Calculate mean, std dev, min, max"""
        values = [r['value'] for r in readings]
        return {
            'sensor_id': readings[0]['sensor_id'],
            'mean': sum(values) / len(values),
            'std_dev': self.calculate_std_dev(values),
            'min': min(values),
            'max': max(values),
            'count': len(values),
            'timestamp': readings[-1]['timestamp']
        }
    
    def detect_anomaly(self, aggregated: Dict) -> bool:
        """Simple anomaly detection based on std dev"""
        # If std dev is too high, likely anomaly
        return aggregated['std_dev'] > aggregated['mean'] * 0.3
```

#### 4. Vision Intelligence Service
```python
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any
import asyncio

class VisionIntelligenceService:
    def __init__(self, model_path: str):
        # Load YOLOv8 model
        self.model = YOLO(model_path)
        self.classes_of_interest = {
            'person': 0,
            'helmet': 1,
            'vest': 2,
            'fire': 3,
            'smoke': 4,
            'fall': 5
        }
    
    async def process_frame(self, frame_data: np.ndarray, camera_id: str) -> Dict[str, Any]:
        """
        Process video frame and detect safety violations
        """
        # Run YOLO inference
        results = self.model(frame_data, conf=0.5)
        
        detections = []
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if confidence > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    detection = {
                        'class_id': class_id,
                        'class_name': self.model.names[class_id],
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2],
                        'area': (x2 - x1) * (y2 - y1)
                    }
                    detections.append(detection)
        
        # Analyze detections for safety violations
        violations = self.analyze_safety_violations(detections, frame_data)
        
        return {
            'camera_id': camera_id,
            'timestamp': datetime.utcnow().isoformat(),
            'detections': detections,
            'violations': violations,
            'risk_score': self.calculate_frame_risk_score(violations)
        }
    
    def analyze_safety_violations(self, detections: List[Dict], frame: np.ndarray) -> List[Dict]:
        """
        Detect PPE violations, restricted zone access, fall detection, etc.
        """
        violations = []
        
        # Group detections by person
        people = [d for d in detections if d['class_name'] == 'person']
        helmets = [d for d in detections if d['class_name'] == 'helmet']
        vests = [d for d in detections if d['class_name'] == 'vest']
        
        # Check for people without helmets
        for person in people:
            nearby_helmets = [h for h in helmets if self.boxes_overlap(person['bbox'], h['bbox'])]
            if not nearby_helmets:
                violations.append({
                    'violation_type': 'MISSING_HELMET',
                    'severity': 'HIGH',
                    'bbox': person['bbox'],
                    'confidence': person['confidence']
                })
        
        # Check for restricted zone access
        # (Assuming restricted zones are pre-defined in DB)
        restricted_zones = self.get_restricted_zones()  # From DB
        for person in people:
            if self.is_in_restricted_zone(person['bbox'], restricted_zones):
                violations.append({
                    'violation_type': 'RESTRICTED_ZONE_ACCESS',
                    'severity': 'CRITICAL',
                    'zone': self.get_zone_name(person['bbox']),
                    'bbox': person['bbox']
                })
        
        return violations
    
    def boxes_overlap(self, box1: List[int], box2: List[int], threshold: float = 0.3) -> bool:
        """Check if two bounding boxes overlap"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Calculate intersection
        inter_width = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        inter_height = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        inter_area = inter_width * inter_height
        
        # Calculate union
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        iou = inter_area / union_area if union_area > 0 else 0
        return iou > threshold
    
    def calculate_frame_risk_score(self, violations: List[Dict]) -> float:
        """
        Calculate overall risk score for frame based on violations
        """
        if not violations:
            return 0.0
        
        severity_scores = {
            'LOW': 10,
            'MEDIUM': 30,
            'HIGH': 60,
            'CRITICAL': 100
        }
        
        max_score = max(severity_scores.get(v['severity'], 0) for v in violations)
        return min(max_score, 100.0)
```

#### 5. Risk Prediction Service
```python
import xgboost as xgb
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class RiskPredictionService:
    def __init__(self, model_path: str):
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
        
        self.feature_names = [
            'gas_level', 'pressure', 'temperature', 'humidity',
            'vibration', 'maintenance_active', 'worker_count',
            'permit_type_weight', 'shift_type', 'time_of_day',
            'historical_incidents', 'equipment_age'
        ]
    
    def predict_risk(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict risk probability and classify risk level
        """
        # Create feature vector in correct order
        feature_vector = np.array([[
            features.get(fname, 0.0) for fname in self.feature_names
        ]])
        
        # Get prediction probability
        risk_probability = self.model.predict_proba(feature_vector)[0][1]
        risk_class = self.model.predict(feature_vector)[0]
        
        # Get feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        
        # Classify risk level
        if risk_probability < 0.25:
            risk_level = 'LOW'
            risk_score = int(risk_probability * 25)
        elif risk_probability < 0.50:
            risk_level = 'MEDIUM'
            risk_score = 25 + int((risk_probability - 0.25) * 100)
        elif risk_probability < 0.75:
            risk_level = 'HIGH'
            risk_score = 50 + int((risk_probability - 0.50) * 100)
        else:
            risk_level = 'CRITICAL'
            risk_score = 75 + int((risk_probability - 0.75) * 100)
        
        return {
            'risk_probability': float(risk_probability),
            'risk_level': risk_level,
            'risk_score': risk_score,
            'timestamp': datetime.utcnow().isoformat(),
            'top_risk_factors': sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'explanation': self.generate_risk_explanation(risk_level, feature_importance)
        }
    
    def generate_risk_explanation(self, risk_level: str, features: Dict[str, float]) -> str:
        """Generate human-readable risk explanation"""
        top_factors = sorted(features.items(), key=lambda x: x[1], reverse=True)[:3]
        
        explanation = f"Risk Level: {risk_level}. "
        explanation += "Contributing factors: "
        explanation += ", ".join([f"{f[0]} ({f[1]:.2f})" for f in top_factors])
        
        return explanation
    
    def get_compound_risk(self, gas_reading: float, maintenance_active: bool,
                         worker_count: int, permit_active: bool) -> Dict[str, Any]:
        """
        Calculate compound risk (the core PS-1 feature)
        """
        gas_risk = self.normalize_gas_risk(gas_reading)
        maintenance_risk = 0.6 if maintenance_active else 0.0
        worker_risk = min(worker_count / 10.0, 1.0)  # Normalize to 0-1
        permit_risk = 0.7 if permit_active else 0.0
        
        # Weighted sum of risk factors
        compound_risk = (
            gas_risk * 0.40 +
            maintenance_risk * 0.25 +
            worker_risk * 0.20 +
            permit_risk * 0.15
        )
        
        return {
            'compound_risk_score': compound_risk,
            'risk_breakdown': {
                'gas_risk': gas_risk,
                'maintenance_risk': maintenance_risk,
                'worker_density_risk': worker_risk,
                'permit_risk': permit_risk
            },
            'risk_type': 'COMPOUND',
            'trigger_point': 'Multiple conditions detected simultaneously'
        }
    
    def normalize_gas_risk(self, gas_ppm: float) -> float:
        """Normalize gas reading to risk score"""
        if gas_ppm < 50:
            return 0.0
        elif gas_ppm < 100:
            return (gas_ppm - 50) / 50 * 0.3
        elif gas_ppm < 150:
            return 0.3 + (gas_ppm - 100) / 50 * 0.4
        else:
            return min(0.7 + (gas_ppm - 150) / 100 * 0.3, 1.0)
```

#### 6. Knowledge Graph Service
```python
from neo4j import GraphDatabase
from typing import Dict, List, Any

class KnowledgeGraphService:
    def __init__(self, uri: str, auth: tuple):
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def create_worker_node(self, worker_id: str, name: str, role: str, shift: str):
        """Create worker node in knowledge graph"""
        with self.driver.session() as session:
            session.run(
                """
                CREATE (w:Worker {
                    worker_id: $worker_id,
                    name: $name,
                    role: $role,
                    shift: $shift
                })
                """,
                worker_id=worker_id,
                name=name,
                role=role,
                shift=shift
            )
    
    def create_equipment_node(self, equipment_id: str, equipment_type: str, location: str):
        """Create equipment node"""
        with self.driver.session() as session:
            session.run(
                """
                CREATE (e:Equipment {
                    equipment_id: $equipment_id,
                    type: $equipment_type,
                    location: $location
                })
                """,
                equipment_id=equipment_id,
                equipment_type=equipment_type,
                location=location
            )
    
    def create_relationship(self, from_node_id: str, from_type: str,
                          rel_type: str, to_node_id: str, to_type: str):
        """Create relationship between nodes"""
        with self.driver.session() as session:
            session.run(
                f"""
                MATCH (from:{from_type} {{{{id: $from_id}}}})
                MATCH (to:{to_type} {{{{id: $to_id}}}})
                CREATE (from)-[:{rel_type}]->(to)
                """,
                from_id=from_node_id,
                to_id=to_node_id
            )
    
    def query_compound_risk(self, sensor_id: str) -> List[Dict[str, Any]]:
        """
        Query graph to find compound risk conditions
        Returns: workers near high-risk sensors with active permits
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Sensor {sensor_id: $sensor_id})-[:MONITORS]->(eq:Equipment)
                MATCH (eq)<-[:LOCATED_IN]-(z:Zone)
                MATCH (w:Worker)-[:WORKS_IN]->(z)
                MATCH (w)-[:HAS_PERMIT]->(p:Permit)
                WHERE p.status = 'ACTIVE'
                RETURN w.worker_id, w.name, eq.equipment_id, p.permit_type, z.zone_name
                """,
                sensor_id=sensor_id
            )
            
            return [dict(record) for record in result]
    
    def identify_risk_patterns(self) -> List[Dict[str, Any]]:
        """
        Identify patterns that could lead to incidents
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (w:Worker)-[:WORKS_IN]->(z:Zone)
                MATCH (s:Sensor {type: 'GAS'})-[:MONITORS]->(eq:Equipment)-[:LOCATED_IN]->(z)
                MATCH (eq)-[:REQUIRES_MAINTENANCE]->(m:Maintenance {status: 'ACTIVE'})
                MATCH (w)-[:HAS_PERMIT]->(p:Permit {type: 'HOT_WORK', status: 'ACTIVE'})
                RETURN z.zone_name, count(w) as worker_count, s.current_level as gas_level
                """
            )
            
            patterns = [dict(record) for record in result]
            return [p for p in patterns if p['gas_level'] > 100 and p['worker_count'] > 0]
```

#### 7. Emergency Response Service
```python
from typing import Dict, List, Any
from datetime import datetime
import json

class EmergencyResponseService:
    def __init__(self, config: Dict):
        self.config = config
        self.notification_service = None  # Injected
        self.geospatial_service = None    # Injected
    
    def trigger_emergency_response(self, risk_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate emergency response workflow
        """
        incident_id = self.generate_incident_id()
        
        # Step 1: Calculate evacuation routes
        evacuation_plan = self.calculate_evacuation_routes(
            affected_zones=risk_alert.get('affected_zones', []),
            hazard_type=risk_alert.get('hazard_type')
        )
        
        # Step 2: Assign response teams
        team_assignments = self.assign_response_teams(
            affected_zones=risk_alert.get('affected_zones', []),
            incident_type=risk_alert.get('hazard_type')
        )
        
        # Step 3: Generate incident report
        incident_report = self.generate_incident_report(
            incident_id=incident_id,
            risk_alert=risk_alert,
            evacuation_plan=evacuation_plan
        )
        
        # Step 4: Generate regulatory report
        regulatory_report = self.generate_regulatory_report(
            incident_report=incident_report,
            applicable_standards=['OISD-STD-105', 'Factory Act']
        )
        
        # Step 5: Send notifications
        self.send_emergency_notifications(
            incident_id=incident_id,
            evacuation_plan=evacuation_plan,
            team_assignments=team_assignments
        )
        
        return {
            'incident_id': incident_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'ACTIVE',
            'evacuation_plan': evacuation_plan,
            'team_assignments': team_assignments,
            'incident_report_url': f'/api/v1/incidents/{incident_id}/report',
            'regulatory_report_url': f'/api/v1/incidents/{incident_id}/regulatory'
        }
    
    def calculate_evacuation_routes(self, affected_zones: List[str], hazard_type: str) -> Dict:
        """
        Calculate optimal evacuation routes for affected zones
        """
        # Get plant map and zones
        plant_map = self.geospatial_service.get_plant_map()
        
        # Identify safe assembly points
        assembly_points = self.geospatial_service.get_assembly_points()
        
        # Calculate routes for each zone
        routes = {}
        for zone in affected_zones:
            zone_location = plant_map.get(zone)
            
            # Find nearest safe assembly point
            nearest_point = min(
                assembly_points,
                key=lambda p: self.calculate_distance(zone_location, p)
            )
            
            routes[zone] = {
                'zone': zone,
                'assembly_point': nearest_point['name'],
                'estimated_time': self.estimate_evacuation_time(zone, nearest_point),
                'route_description': self.get_route_description(zone, nearest_point),
                'worker_count': self.get_worker_count_in_zone(zone)
            }
        
        return {
            'incident_type': 'EVACUATION',
            'priority': 'CRITICAL',
            'routes': routes,
            'total_workers_affected': sum(r['worker_count'] for r in routes.values()),
            'all_clear_signal': f'/api/v1/emergency/{self.last_incident_id}/all-clear'
        }
    
    def assign_response_teams(self, affected_zones: List[str], incident_type: str) -> Dict:
        """
        Assign trained response teams to handle emergency
        """
        response_teams = self.get_available_response_teams()
        
        assignments = {}
        for zone in affected_zones:
            # Find best-trained team for incident type
            best_team = self.find_best_team(response_teams, incident_type)
            
            assignments[zone] = {
                'team_id': best_team['team_id'],
                'team_members': best_team['members'],
                'leader': best_team['leader'],
                'equipment': best_team['equipment'],
                'estimated_arrival': self.estimate_arrival_time(best_team, zone),
                'instructions': self.get_team_instructions(incident_type)
            }
        
        return assignments
    
    def generate_incident_report(self, incident_id: str, risk_alert: Dict,
                                evacuation_plan: Dict) -> Dict:
        """
        Generate comprehensive incident report
        """
        return {
            'incident_id': incident_id,
            'timestamp': datetime.utcnow().isoformat(),
            'hazard_type': risk_alert.get('hazard_type'),
            'risk_level': risk_alert.get('risk_level'),
            'affected_zones': risk_alert.get('affected_zones'),
            'root_cause': risk_alert.get('predicted_cause'),
            'contributing_factors': risk_alert.get('contributing_factors', []),
            'evacuation_plan': evacuation_plan,
            'response_teams_assigned': risk_alert.get('team_count', 0),
            'estimated_resolution_time': '4 hours',
            'preliminary_recommendations': self.get_recommendations(risk_alert)
        }
    
    def generate_regulatory_report(self, incident_report: Dict, applicable_standards: List[str]) -> Dict:
        """
        Generate regulatory-compliant incident report
        """
        return {
            'report_type': 'INCIDENT_NOTIFICATION',
            'applicable_standards': applicable_standards,
            'incident_details': incident_report,
            'regulatory_requirements': {
                'OISD-STD-105': {
                    'requirement': 'Immediate notification within 15 minutes',
                    'compliance_status': 'MET',
                    'notified_at': datetime.utcnow().isoformat()
                },
                'Factory Act': {
                    'requirement': 'Detailed report within 48 hours',
                    'compliance_status': 'IN_PROGRESS',
                    'due_date': datetime.utcnow().isoformat()
                }
            },
            'prepared_by': 'SentinelAI System',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def send_emergency_notifications(self, incident_id: str, evacuation_plan: Dict,
                                    team_assignments: Dict):
        """
        Send emergency notifications through multiple channels
        """
        # Send SMS alerts
        self.notification_service.send_sms_alert(
            recipients=['supervisor', 'safety_manager'],
            message=f"EMERGENCY: Evacuation initiated. Incident ID: {incident_id}"
        )
        
        # Send mobile push notifications
        self.notification_service.send_push_notification(
            incident_id=incident_id,
            title="EMERGENCY EVACUATION",
            body="Follow evacuation routes displayed in app",
            zones=list(evacuation_plan['routes'].keys())
        )
        
        # Trigger alarm systems
        self.notification_service.trigger_sirens(
            zones=list(evacuation_plan['routes'].keys()),
            pattern='CONTINUOUS'
        )
        
        # Send email to management
        self.notification_service.send_email(
            recipients=['plant_manager', 'safety_head'],
            subject=f"CRITICAL: Emergency Response Activated - {incident_id}",
            body=json.dumps(evacuation_plan, indent=2)
        )
```

---

## FRONTEND ARCHITECTURE

### Frontend Technology Stack
- **Web Dashboard:** React 18 + TypeScript + Redux
- **Mobile App:** React Native / Flutter
- **Real-time:** WebSocket + Socket.io
- **Styling:** Tailwind CSS + styled-components
- **State Management:** Redux Toolkit
- **UI Components:** Material-UI / Ant Design
- **Charts:** Recharts, Chart.js, Mapbox
- **Build:** Vite, React Native CLI

### Frontend Application Structure

```
frontend/
├── web/                          # Web Dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # Main dashboard
│   │   │   ├── RiskMonitor.tsx    # Real-time risk view
│   │   │   ├── Incidents.tsx      # Incident history
│   │   │   ├── Analytics.tsx      # Analytics & trends
│   │   │   ├── Compliance.tsx     # Compliance status
│   │   │   ├── Settings.tsx       # Admin settings
│   │   │   └── Login.tsx          # Authentication
│   │   ├── components/
│   │   │   ├── RiskHeatmap.tsx
│   │   │   ├── DigitalTwin.tsx
│   │   │   ├── AlertPanel.tsx
│   │   │   ├── SensorMonitor.tsx
│   │   │   ├── EvacuationMap.tsx
│   │   │   └── PermitTracker.tsx
│   │   ├── services/
│   │   │   ├── api.ts            # API calls
│   │   │   ├── websocket.ts      # WebSocket handler
│   │   │   ├── auth.ts           # Authentication
│   │   │   └── notifications.ts  # Push notifications
│   │   ├── store/                # Redux store
│   │   │   ├── slices/
│   │   │   │   ├── riskSlice.ts
│   │   │   │   ├── sensorSlice.ts
│   │   │   │   ├── incidentSlice.ts
│   │   │   │   └── uiSlice.ts
│   │   │   └── store.ts
│   │   ├── types/
│   │   │   ├── sensor.ts
│   │   │   ├── risk.ts
│   │   │   ├── incident.ts
│   │   │   └── api.ts
│   │   └── index.tsx
│   └── public/
│
├── mobile/                       # Mobile App (React Native)
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.tsx
│   │   │   ├── RiskAlertScreen.tsx
│   │   │   ├── EvacuationScreen.tsx
│   │   │   ├── ReportScreen.tsx
│   │   │   └── ProfileScreen.tsx
│   │   ├── components/
│   │   ├── services/
│   │   ├── store/
│   │   └── App.tsx
│   └── package.json
│
└── shared/                       # Shared utilities
    ├── api-client.ts
    ├── types.ts
    └── constants.ts
```

### Web Dashboard Component Architecture

#### 1. Main Dashboard Page
```typescript
// pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useWebSocket } from '../hooks/useWebSocket';
import RiskHeatmap from '../components/RiskHeatmap';
import SensorMonitor from '../components/SensorMonitor';
import AlertPanel from '../components/AlertPanel';
import KPICard from '../components/KPICard';
import PermitTracker from '../components/PermitTracker';

export const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const { currentRisk, alerts, sensors } = useSelector(state => state.risk);
  const [timeRange, setTimeRange] = useState('24h');
  
  // Real-time WebSocket connection
  const { data: realtimeData, connected } = useWebSocket('/api/v1/ws/dashboard');
  
  useEffect(() => {
    // Fetch initial data
    dispatch(fetchDashboardData());
    
    // Update from WebSocket
    if (realtimeData) {
      dispatch(updateRiskData(realtimeData));
    }
  }, [realtimeData]);
  
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Safety Intelligence Dashboard</h1>
        <div className="connection-status">
          {connected ? (
            <span className="status-online">🟢 Live</span>
          ) : (
            <span className="status-offline">🔴 Offline</span>
          )}
        </div>
      </header>
      
      <section className="kpi-section">
        <KPICard
          title="Overall Risk Score"
          value={currentRisk.score}
          unit="%"
          trend="down"
          status={currentRisk.level}
        />
        <KPICard
          title="Active Alerts"
          value={alerts.length}
          trend="stable"
          status={alerts.length > 0 ? 'warning' : 'normal'}
        />
        <KPICard
          title="Workers in Risk Zones"
          value={currentRisk.workersAtRisk}
          trend="down"
          status={currentRisk.workersAtRisk > 0 ? 'warning' : 'normal'}
        />
        <KPICard
          title="System Uptime"
          value="99.8"
          unit="%"
          trend="up"
          status="normal"
        />
      </section>
      
      <section className="main-content">
        <div className="left-panel">
          <RiskHeatmap />
          <PermitTracker />
        </div>
        
        <div className="center-panel">
          <AlertPanel alerts={alerts} />
        </div>
        
        <div className="right-panel">
          <SensorMonitor sensors={sensors} />
        </div>
      </section>
    </div>
  );
};
```

#### 2. Risk Heatmap Component
```typescript
// components/RiskHeatmap.tsx
import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import Mapbox from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface Zone {
  id: string;
  name: string;
  coordinates: [number, number];
  riskScore: number;
  workers: number;
  hazards: string[];
}

const RiskHeatmap: React.FC = () => {
  const zones = useSelector(state => state.geospatial.zones);
  const [viewport, setViewport] = React.useState({
    latitude: 20.5937,
    longitude: 78.9629,
    zoom: 12
  });
  
  const getZoneColor = (riskScore: number): string => {
    if (riskScore >= 75) return '#FF0000';      // Red - Critical
    if (riskScore >= 50) return '#FFA500';      // Orange - High
    if (riskScore >= 25) return '#FFFF00';      // Yellow - Medium
    return '#00FF00';                           // Green - Low
  };
  
  return (
    <div className="heatmap-container">
      <Mapbox
        {...viewport}
        onViewportChange={setViewport}
        mapboxApiAccessToken={process.env.REACT_APP_MAPBOX_TOKEN}
        style={{ width: '100%', height: '500px' }}
      >
        {zones.map((zone: Zone) => (
          <div
            key={zone.id}
            className="zone-marker"
            style={{
              backgroundColor: getZoneColor(zone.riskScore),
              opacity: 0.7,
              borderRadius: '50%',
              padding: '10px',
              cursor: 'pointer'
            }}
            onClick={() => handleZoneClick(zone)}
          >
            <div className="zone-info">
              <span className="zone-name">{zone.name}</span>
              <span className="risk-score">{zone.riskScore}%</span>
              <span className="worker-count">👥 {zone.workers}</span>
            </div>
          </div>
        ))}
      </Mapbox>
      
      <div className="legend">
        <div className="legend-item"><span style={{color: '#FF0000'}}>█</span> Critical (75-100)</div>
        <div className="legend-item"><span style={{color: '#FFA500'}}>█</span> High (50-74)</div>
        <div className="legend-item"><span style={{color: '#FFFF00'}}>█</span> Medium (25-49)</div>
        <div className="legend-item"><span style={{color: '#00FF00'}}>█</span> Low (0-24)</div>
      </div>
    </div>
  );
};

export default RiskHeatmap;
```

#### 3. Alert Panel Component
```typescript
// components/AlertPanel.tsx
import React from 'react';
import { Alert } from '../types/incident';

interface AlertPanelProps {
  alerts: Alert[];
}

const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  const getSeverityClass = (severity: string): string => {
    switch(severity) {
      case 'CRITICAL': return 'alert-critical';
      case 'HIGH': return 'alert-high';
      case 'MEDIUM': return 'alert-medium';
      case 'LOW': return 'alert-low';
      default: return 'alert-normal';
    }
  };
  
  return (
    <div className="alert-panel">
      <h2>Active Alerts</h2>
      
      {alerts.length === 0 ? (
        <div className="no-alerts">
          <p>✓ No active alerts</p>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map(alert => (
            <div
              key={alert.id}
              className={`alert-item ${getSeverityClass(alert.severity)}`}
            >
              <div className="alert-header">
                <span className="alert-title">{alert.title}</span>
                <span className="alert-time">{new Date(alert.timestamp).toLocaleTimeString()}</span>
              </div>
              
              <div className="alert-body">
                <p>{alert.description}</p>
                
                {alert.affectedZones && alert.affectedZones.length > 0 && (
                  <div className="affected-zones">
                    <strong>Zones: </strong>
                    {alert.affectedZones.join(', ')}
                  </div>
                )}
                
                {alert.recommendedAction && (
                  <div className="recommendation">
                    <strong>Recommended Action:</strong>
                    <p>{alert.recommendedAction}</p>
                  </div>
                )}
              </div>
              
              <div className="alert-actions">
                <button onClick={() => handleAcknowledge(alert.id)}>
                  Acknowledge
                </button>
                <button onClick={() => handleDetails(alert.id)}>
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
```

#### 4. Digital Twin Component
```typescript
// components/DigitalTwin.tsx
import React, { useEffect } from 'react';
import * as THREE from 'three';

const DigitalTwin: React.FC = () => {
  const mountRef = React.useRef<HTMLDivElement>(null);
  const sceneRef = React.useRef<THREE.Scene | null>(null);
  
  useEffect(() => {
    if (!mountRef.current) return;
    
    // Initialize Three.js scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    
    renderer.setSize(
      mountRef.current.clientWidth,
      mountRef.current.clientHeight
    );
    mountRef.current.appendChild(renderer.domElement);
    
    // Add plant elements
    // Equipment
    const boilerGeometry = new THREE.BoxGeometry(2, 3, 2);
    const boilerMaterial = new THREE.MeshBasicMaterial({ color: 0x888888 });
    const boiler = new THREE.Mesh(boilerGeometry, boilerMaterial);
    boiler.position.set(-5, 0, 0);
    scene.add(boiler);
    
    // Sensors (small spheres)
    const sensorGeometry = new THREE.SphereGeometry(0.3, 32, 32);
    const sensorMaterial = new THREE.MeshBasicMaterial({ color: 0x00FF00 });
    const sensor = new THREE.Mesh(sensorGeometry, sensorMaterial);
    sensor.position.set(-5, 3, 0);
    scene.add(sensor);
    
    // Workers (cylinders)
    const workerGeometry = new THREE.CylinderGeometry(0.5, 0.5, 1.8, 32);
    const workerMaterial = new THREE.MeshBasicMaterial({ color: 0xFFFF00 });
    const worker = new THREE.Mesh(workerGeometry, workerMaterial);
    worker.position.set(0, 0.9, 0);
    scene.add(worker);
    
    // Add lighting
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(5, 10, 5);
    scene.add(light);
    
    camera.position.z = 15;
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Rotate scene slightly
      scene.rotation.y += 0.001;
      
      renderer.render(scene, camera);
    };
    
    animate();
    
    sceneRef.current = scene;
    
    return () => {
      mountRef.current?.removeChild(renderer.domElement);
    };
  }, []);
  
  return <div ref={mountRef} style={{ width: '100%', height: '600px' }} />;
};

export default DigitalTwin;
```

### Frontend State Management (Redux)

```typescript
// store/slices/riskSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export interface RiskState {
  currentRisk: {
    score: number;
    level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    workersAtRisk: number;
    affectedZones: string[];
  };
  historicalData: Array<{
    timestamp: string;
    score: number;
  }>;
  loading: boolean;
  error: string | null;
}

const initialState: RiskState = {
  currentRisk: {
    score: 0,
    level: 'LOW',
    workersAtRisk: 0,
    affectedZones: []
  },
  historicalData: [],
  loading: false,
  error: null
};

export const fetchDashboardData = createAsyncThunk(
  'risk/fetchDashboardData',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/v1/risk/current');
      return await response.json();
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const riskSlice = createSlice({
  name: 'risk',
  initialState,
  reducers: {
    updateRiskData: (state, action) => {
      state.currentRisk = action.payload.risk;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.currentRisk = action.payload;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { updateRiskData } = riskSlice.actions;
export default riskSlice.reducer;
```

### Frontend API Client

```typescript
// services/api.ts
import axios, { AxiosInstance } from 'axios';

class APIClient {
  private client: AxiosInstance;
  
  constructor(baseURL: string = process.env.REACT_APP_API_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Add auth token to requests
    this.client.interceptors.request.use(config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }
  
  // Risk endpoints
  async getCurrentRisk() {
    return this.client.get('/api/v1/risk/current');
  }
  
  async getRiskHistory(timeRange: string) {
    return this.client.get(`/api/v1/risk/history?range=${timeRange}`);
  }
  
  async getCompoundRisk(zoneId: string) {
    return this.client.get(`/api/v1/risk/compound/${zoneId}`);
  }
  
  // Sensor endpoints
  async getSensorData(sensorId: string) {
    return this.client.get(`/api/v1/sensors/${sensorId}`);
  }
  
  async getAllSensors() {
    return this.client.get('/api/v1/sensors');
  }
  
  // Incident endpoints
  async getIncidents(filter?: any) {
    return this.client.get('/api/v1/incidents', { params: filter });
  }
  
  async getIncidentDetails(incidentId: string) {
    return this.client.get(`/api/v1/incidents/${incidentId}`);
  }
  
  // Alert endpoints
  async getActiveAlerts() {
    return this.client.get('/api/v1/alerts/active');
  }
  
  async acknowledgeAlert(alertId: string) {
    return this.client.post(`/api/v1/alerts/${alertId}/acknowledge`);
  }
  
  // Emergency endpoints
  async triggerEvacuation(zoneId: string) {
    return this.client.post('/api/v1/emergency/evacuate', { zone_id: zoneId });
  }
  
  async getAllClearEmergency(incidentId: string) {
    return this.client.post(`/api/v1/emergency/${incidentId}/all-clear`);
  }
  
  // Permit endpoints
  async getActivePermits() {
    return this.client.get('/api/v1/permits/active');
  }
  
  async createPermit(permitData: any) {
    return this.client.post('/api/v1/permits', permitData);
  }
  
  // Compliance endpoints
  async getComplianceStatus() {
    return this.client.get('/api/v1/compliance/status');
  }
}

export const apiClient = new APIClient();
```

### Frontend WebSocket Connection

```typescript
// services/websocket.ts
import { useEffect, useState, useCallback } from 'react';
import io, { Socket } from 'socket.io-client';

interface UseWebSocketReturn {
  data: any;
  connected: boolean;
  error: Error | null;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    
    const newSocket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });
    
    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
      newSocket.emit('subscribe', { channels: [url] });
    });
    
    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });
    
    newSocket.on('update', (newData) => {
      setData(newData);
    });
    
    newSocket.on('error', (err) => {
      setError(new Error(err));
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.disconnect();
    };
  }, [url]);
  
  return { data, connected, error };
};
```

---

## AI/ML MODELS & ALGORITHMS

### 1. Vision Models
```python
# YOLO-based Safety Detection
from ultralytics import YOLO
import cv2
import numpy as np

class SafetyVisionModel:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)  # YOLOv8 model
        self.classes = {
            0: 'person',
            1: 'helmet',
            2: 'vest',
            3: 'fire',
            4: 'smoke',
            5: 'fall_detected'
        }
    
    def detect_violations(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect safety violations in frame"""
        results = self.model(frame, conf=0.5)
        
        detections = {
            'objects': [],
            'violations': [],
            'risk_score': 0.0
        }
        
        # Process detections
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if confidence > 0.5:
                    bbox = box.xyxy[0].tolist()
                    detections['objects'].append({
                        'class': self.classes[class_id],
                        'confidence': confidence,
                        'bbox': bbox
                    })
        
        # Analyze for violations
        detections['violations'] = self.analyze_violations(detections['objects'])
        detections['risk_score'] = self.calculate_risk(detections['violations'])
        
        return detections
```

### 2. Risk Prediction Models

```python
# Ensemble Risk Prediction
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class RiskPredictionEnsemble:
    def __init__(self):
        self.xgb_model = xgb.XGBClassifier()
        self.lgb_model = lgb.LGBMClassifier()
        self.rf_model = RandomForestClassifier(n_estimators=100)
        
        # Model weights for ensemble
        self.weights = [0.4, 0.3, 0.3]
    
    def predict_risk(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Ensemble prediction combining XGBoost, LightGBM, and Random Forest
        """
        # Get predictions from each model
        xgb_pred = self.xgb_model.predict_proba(features)[0][1]
        lgb_pred = self.lgb_model.predict_proba(features)[0][1]
        rf_pred = self.rf_model.predict_proba(features)[0][1]
        
        # Weighted ensemble
        ensemble_pred = (
            xgb_pred * self.weights[0] +
            lgb_pred * self.weights[1] +
            rf_pred * self.weights[2]
        )
        
        # Get feature importance
        feature_importance = self.get_ensemble_importance(features)
        
        return {
            'risk_probability': float(ensemble_pred),
            'risk_level': self.classify_risk(ensemble_pred),
            'model_confidence': self.get_ensemble_confidence(),
            'top_factors': feature_importance[:5]
        }
    
    def get_ensemble_importance(self, features: np.ndarray) -> List[Tuple[str, float]]:
        """Get combined feature importance"""
        xgb_importance = self.xgb_model.feature_importances_
        lgb_importance = self.lgb_model.feature_importances_
        rf_importance = self.rf_model.feature_importances_
        
        # Weighted average
        combined = (
            xgb_importance * 0.4 +
            lgb_importance * 0.3 +
            rf_importance * 0.3
        )
        
        feature_names = [
            'gas_level', 'pressure', 'temperature', 'humidity',
            'vibration', 'maintenance_active', 'worker_count'
        ]
        
        return sorted(
            zip(feature_names, combined),
            key=lambda x: x[1],
            reverse=True
        )
```

### 3. Forecasting Models (LSTM)

```python
import tensorflow as tf
from tensorflow import keras
import numpy as np

class TimeSeriesForecaster:
    def __init__(self, lookback: int = 24):
        self.lookback = lookback
        self.model = self.build_model()
    
    def build_model(self) -> keras.Model:
        """Build LSTM model for time-series forecasting"""
        model = keras.Sequential([
            keras.layers.LSTM(64, activation='relu', input_shape=(self.lookback, 1),
                            return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32, activation='relu', return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(6)  # 6 hours ahead
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def forecast(self, historical_data: np.ndarray, steps: int = 6) -> np.ndarray:
        """
        Forecast next N timesteps
        """
        # Normalize data
        data_normalized = self.normalize(historical_data)
        
        # Create sequences
        X = []
        for i in range(len(data_normalized) - self.lookback):
            X.append(data_normalized[i:i+self.lookback])
        X = np.array(X)
        
        # Predict
        predictions = self.model.predict(X[-1:])
        
        return predictions[0]  # Return next 6 hours
    
    def forecast_with_confidence(self, historical_data: np.ndarray) -> Dict[str, Any]:
        """Forecast with confidence intervals using Monte Carlo dropout"""
        predictions = []
        
        # Run multiple predictions (MC Dropout)
        for _ in range(100):
            pred = self.model(
                historical_data.reshape(1, self.lookback, 1),
                training=True
            )
            predictions.append(pred.numpy())
        
        predictions = np.array(predictions)
        
        return {
            'mean': np.mean(predictions, axis=0),
            'std': np.std(predictions, axis=0),
            'lower_bound': np.percentile(predictions, 5, axis=0),
            'upper_bound': np.percentile(predictions, 95, axis=0)
        }
```

### 4. Anomaly Detection

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

class AnomalyDetector:
    def __init__(self, contamination: float = 0.05):
        self.scaler = StandardScaler()
        self.detector = IsolationForest(
            contamination=contamination,
            random_state=42
        )
    
    def fit(self, training_data: np.ndarray):
        """Train anomaly detector"""
        scaled_data = self.scaler.fit_transform(training_data)
        self.detector.fit(scaled_data)
    
    def detect(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect anomalies in sensor data"""
        scaled = self.scaler.transform(data.reshape(1, -1))
        
        # Get anomaly score (-1 for anomaly, 1 for normal)
        prediction = self.detector.predict(scaled)[0]
        anomaly_score = self.detector.score_samples(scaled)[0]
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': float(anomaly_score),  # Range: [-1, 1]
            'confidence': abs(anomaly_score),
            'severity': self.classify_anomaly_severity(anomaly_score)
        }
    
    def classify_anomaly_severity(self, score: float) -> str:
        """Classify severity of anomaly"""
        if score < -0.7:
            return 'CRITICAL'
        elif score < -0.5:
            return 'HIGH'
        elif score < -0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
```

---

## MULTI-AGENT SYSTEM DESIGN

### Agent Architecture

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.last_execution = None
        self.execution_count = 0
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic"""
        pass
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for execution with logging"""
        self.last_execution = datetime.utcnow()
        self.execution_count += 1
        
        result = await self.execute(context)
        
        return {
            'agent_id': self.agent_id,
            'agent_name': self.name,
            'execution_time': datetime.utcnow(),
            'result': result
        }

# agents/vision_agent.py
class VisionAgent(BaseAgent):
    def __init__(self, vision_service):
        super().__init__('vision-agent-001', 'Vision Intelligence Agent')
        self.vision_service = vision_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze CCTV feeds for safety violations
        """
        camera_id = context.get('camera_id')
        frame = context.get('frame')
        
        if not frame:
            return {'status': 'no_frame', 'detections': []}
        
        # Process frame
        detections = await self.vision_service.process_frame(frame, camera_id)
        
        # Analyze violations
        violations = detections.get('violations', [])
        
        return {
            'camera_id': camera_id,
            'detections_count': len(detections['objects']),
            'violations': violations,
            'risk_score': detections['risk_score'],
            'requires_alert': len(violations) > 0
        }

# agents/sensor_agent.py
class SensorAgent(BaseAgent):
    def __init__(self, sensor_service):
        super().__init__('sensor-agent-001', 'Sensor Intelligence Agent')
        self.sensor_service = sensor_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze IoT sensor readings
        """
        sensor_data = context.get('sensor_data', {})
        
        analysis = {
            'sensor_analysis': {},
            'anomalies': [],
            'alerts': []
        }
        
        for sensor_id, reading in sensor_data.items():
            # Detect anomalies
            anomaly_result = self.sensor_service.detect_anomaly(sensor_id, reading)
            
            if anomaly_result['is_anomaly']:
                analysis['anomalies'].append({
                    'sensor_id': sensor_id,
                    'value': reading,
                    'severity': anomaly_result['severity']
                })
            
            analysis['sensor_analysis'][sensor_id] = anomaly_result
        
        return analysis

# agents/risk_agent.py
class RiskAgent(BaseAgent):
    def __init__(self, risk_service):
        super().__init__('risk-agent-001', 'Risk Prediction Agent')
        self.risk_service = risk_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict current and future risk
        """
        features = context.get('features', {})
        
        # Current risk prediction
        current_risk = self.risk_service.predict_risk(features)
        
        # Compound risk detection (PS-1 core feature)
        compound_risk = self.risk_service.get_compound_risk(
            gas_reading=features.get('gas_level', 0),
            maintenance_active=features.get('maintenance_active', False),
            worker_count=features.get('worker_count', 0),
            permit_active=features.get('permit_active', False)
        )
        
        return {
            'current_risk': current_risk,
            'compound_risk': compound_risk,
            'risk_factors': current_risk.get('top_risk_factors'),
            'requires_alert': current_risk['risk_level'] in ['HIGH', 'CRITICAL']
        }

# agents/compliance_agent.py
class ComplianceAgent(BaseAgent):
    def __init__(self, compliance_service):
        super().__init__('compliance-agent-001', 'Compliance Intelligence Agent')
        self.compliance_service = compliance_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check regulatory compliance
        """
        incident = context.get('incident', {})
        current_conditions = context.get('current_conditions', {})
        
        # Check against regulations
        compliance_checks = {
            'OISD-STD-105': self.compliance_service.check_oisd_compliance(current_conditions),
            'Factory Act': self.compliance_service.check_factory_act_compliance(current_conditions),
            'DGMS': self.compliance_service.check_dgms_compliance(current_conditions)
        }
        
        # Get relevant guidance
        guidance = self.compliance_service.get_rag_guidance(
            query=f"Similar incident: {incident.get('type')}"
        )
        
        return {
            'compliance_status': compliance_checks,
            'compliance_gaps': [k for k, v in compliance_checks.items() if not v['compliant']],
            'relevant_regulations': guidance,
            'recommendations': self.compliance_service.get_recommendations(compliance_checks)
        }

# agents/supervisor_agent.py
class SupervisorAgent(BaseAgent):
    def __init__(self, agents: Dict[str, BaseAgent]):
        super().__init__('supervisor-agent-001', 'Supervisor Agent')
        self.agents = agents
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate all agents and make final decision
        """
        import asyncio
        
        # Execute all agents in parallel
        agent_tasks = {
            name: agent.run(context)
            for name, agent in self.agents.items()
        }
        
        results = {}
        for name, task in agent_tasks.items():
            results[name] = await task
        
        # Synthesize results
        final_decision = self.synthesize_results(results, context)
        
        return final_decision
    
    def synthesize_results(self, agent_results: Dict, context: Dict) -> Dict[str, Any]:
        """Combine results from all agents"""
        # Extract risk signals
        risk_level = agent_results['risk_agent']['result']['current_risk']['risk_level']
        violations = agent_results['vision_agent']['result']['violations']
        anomalies = agent_results['sensor_agent']['result']['anomalies']
        compound_risk = agent_results['risk_agent']['result']['compound_risk']
        
        # Determine if emergency response needed
        needs_emergency = (
            risk_level == 'CRITICAL' or
            len(violations) > 3 or
            compound_risk.get('compound_risk_score', 0) > 0.7
        )
        
        return {
            'final_risk_level': risk_level,
            'needs_emergency_response': needs_emergency,
            'all_agent_results': agent_results,
            'recommended_actions': self.get_recommendations(
                risk_level, violations, anomalies
            ),
            'decision_timestamp': datetime.utcnow().isoformat()
        }
```

---

## DATABASE & STORAGE SCHEMAS

### 1. PostgreSQL Schemas

```sql
-- PostgreSQL - Structured Data

-- Users and Access Control
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM ('admin', 'safety_manager', 'operator', 'viewer'),
    department VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Equipment Registry
CREATE TABLE equipment (
    equipment_id VARCHAR(50) PRIMARY KEY,
    equipment_type VARCHAR(100) NOT NULL,
    location_zone VARCHAR(10),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    installation_date DATE,
    last_maintenance TIMESTAMP,
    next_maintenance TIMESTAMP,
    health_score FLOAT DEFAULT 100.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensors
CREATE TABLE sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,
    sensor_type VARCHAR(50) NOT NULL,
    equipment_id VARCHAR(50) REFERENCES equipment(equipment_id),
    location_zone VARCHAR(10),
    unit_of_measurement VARCHAR(20),
    min_threshold FLOAT,
    max_threshold FLOAT,
    is_active BOOLEAN DEFAULT true,
    calibration_date DATE,
    accuracy_rating FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workers
CREATE TABLE workers (
    worker_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(100),
    department VARCHAR(100),
    training_level ENUM ('junior', 'intermediate', 'senior'),
    assigned_zone VARCHAR(10),
    rfid_tag_id VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permits
CREATE TABLE permits (
    permit_id VARCHAR(50) PRIMARY KEY,
    permit_type VARCHAR(50) NOT NULL,
    issued_by VARCHAR(255),
    issued_date TIMESTAMP NOT NULL,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    location_zone VARCHAR(10),
    authorized_workers TEXT[],
    equipment_affected TEXT[],
    precautions TEXT[],
    status ENUM ('pending', 'active', 'expired', 'cancelled', 'completed'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incidents
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY,
    incident_type VARCHAR(100) NOT NULL,
    date_time TIMESTAMP NOT NULL,
    location_zone VARCHAR(10),
    severity ENUM ('low', 'medium', 'high', 'critical'),
    description TEXT,
    workers_involved TEXT[],
    equipment_involved TEXT[],
    root_cause TEXT,
    contributing_factors TEXT[],
    corrective_actions TEXT[],
    status ENUM ('open', 'investigating', 'resolved', 'closed'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

-- Alerts
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY,
    alert_type VARCHAR(100) NOT NULL,
    severity ENUM ('low', 'medium', 'high', 'critical'),
    title VARCHAR(255),
    description TEXT,
    affected_zones TEXT[],
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    changes JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

-- Create Indexes
CREATE INDEX idx_sensors_equipment_id ON sensors(equipment_id);
CREATE INDEX idx_sensors_zone ON sensors(location_zone);
CREATE INDEX idx_workers_zone ON workers(assigned_zone);
CREATE INDEX idx_permits_status ON permits(status);
CREATE INDEX idx_permits_datetime ON permits(start_datetime, end_datetime);
CREATE INDEX idx_incidents_type ON incidents(incident_type);
CREATE INDEX idx_incidents_date ON incidents(date_time);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created ON alerts(created_at);
```

### 2. InfluxDB Schemas (Time-Series Data)

```
# InfluxDB - Time-Series Data
# Database: sentinel_metrics

# Sensor Readings
measurement: sensor_reading
  tags:
    sensor_id: string
    sensor_type: string
    zone: string
    equipment_id: string
  fields:
    value: float
    status: string
    confidence: float
  timestamp: nanoseconds

# SCADA Data
measurement: scada_metrics
  tags:
    equipment_id: string
    equipment_type: string
    zone: string
  fields:
    run_status: string
    power_consumption: float
    efficiency: float
    temperature: float
    vibration: float
  timestamp: nanoseconds

# Risk Scores
measurement: risk_score
  tags:
    zone_id: string
    risk_type: string
  fields:
    risk_score: float
    risk_level: string
    gas_risk: float
    worker_risk: float
    maintenance_risk: float
  timestamp: nanoseconds

# Alert Events
measurement: alert_event
  tags:
    alert_id: string
    alert_type: string
    severity: string
  fields:
    is_acknowledged: boolean
    response_time_seconds: integer
  timestamp: nanoseconds
```

### 3. Neo4j Knowledge Graph Schemas

```cypher
// Neo4j - Knowledge Graph Schema

// Nodes
CREATE (w:Worker {
  worker_id: string,
  name: string,
  role: string,
  training_level: string
})

CREATE (e:Equipment {
  equipment_id: string,
  type: string,
  location: string,
  health_score: float
})

CREATE (s:Sensor {
  sensor_id: string,
  type: string,
  unit: string
})

CREATE (z:Zone {
  zone_id: string,
  name: string,
  risk_level: string
})

CREATE (p:Permit {
  permit_id: string,
  type: string,
  status: string
})

CREATE (h:Hazard {
  hazard_id: string,
  type: string,
  severity: string
})

CREATE (i:Incident {
  incident_id: string,
  type: string,
  severity: string
})

// Relationships
MATCH (w:Worker), (z:Zone)
CREATE (w)-[:WORKS_IN]->(z)

MATCH (e:Equipment), (z:Zone)
CREATE (e)-[:LOCATED_IN]->(z)

MATCH (s:Sensor), (e:Equipment)
CREATE (s)-[:MONITORS]->(e)

MATCH (p:Permit), (e:Equipment)
CREATE (p)-[:AFFECTS]->(e)

MATCH (w:Worker), (p:Permit)
CREATE (w)-[:HAS_PERMIT]->(p)

MATCH (h:Hazard), (z:Zone)
CREATE (h)-[:EXISTS_IN]->(z)

MATCH (e:Equipment), (h:Hazard)
CREATE (e)-[:CAN_CAUSE]->(h)

MATCH (i:Incident), (h:Hazard)
CREATE (i)-[:CAUSED_BY]->(h)

MATCH (i:Incident), (w:Worker)
CREATE (i)-[:INVOLVED]->(w)

// Indexes
CREATE INDEX idx_worker_id FOR (w:Worker) ON (w.worker_id);
CREATE INDEX idx_equipment_id FOR (e:Equipment) ON (e.equipment_id);
CREATE INDEX idx_zone_id FOR (z:Zone) ON (z.zone_id);
CREATE INDEX idx_permit_status FOR (p:Permit) ON (p.status);
```

### 4. MongoDB Schemas (Document Storage)

```json
// MongoDB - Document Storage

// Compliance Documents
{
  "_id": ObjectId,
  "document_type": "regulation",
  "title": "OISD-STD-105",
  "content": "...",
  "sections": [
    {
      "section_number": "1",
      "title": "...",
      "content": "..."
    }
  ],
  "keywords": ["gas_safety", "confined_space"],
  "embeddings": [0.1, 0.2, 0.3, ...],
  "indexed_at": ISODate()
}

// Incident Reports
{
  "_id": ObjectId,
  "incident_id": "INC-2025-001",
  "incident_type": "gas_leak",
  "date_time": ISODate(),
  "location": "Zone A",
  "description": "...",
  "investigation_notes": "...",
  "similar_incidents": ["INC-2024-005", "INC-2024-012"],
  "lessons_learned": "...",
  "preventive_measures": ["..."],
  "tags": ["gas", "pressure", "maintenance"],
  "created_by": "safety_officer_001",
  "created_at": ISODate()
}

// Near-Miss Reports
{
  "_id": ObjectId,
  "near_miss_id": "NM-2025-001",
  "type": "potential_gas_leak",
  "date": ISODate(),
  "zone": "Zone B",
  "description": "...",
  "potential_severity": "high",
  "root_cause_analysis": "...",
  "corrective_actions": ["action_1", "action_2"],
  "status": "open",
  "assigned_to": "maintenance_team_01"
}
```

---

## API SPECIFICATIONS

### RESTful API Endpoints

```
# Base URL: /api/v1

# AUTHENTICATION
POST   /auth/login                    # User login
POST   /auth/logout                   # User logout
POST   /auth/refresh-token           # Refresh JWT token
POST   /auth/register                # User registration (admin only)

# RISK & SAFETY
GET    /risk/current                 # Get current risk status
GET    /risk/history                 # Risk history (with time range)
GET    /risk/compound/{zone_id}      # Compound risk for zone
POST   /risk/forecast                # Predict future risk
GET    /risk/trend                   # Risk trend analysis

# SENSORS & DATA
GET    /sensors                      # List all sensors
GET    /sensors/{sensor_id}          # Get sensor details
GET    /sensors/{sensor_id}/readings # Get sensor readings
POST   /sensors/data                 # Ingest sensor data
GET    /sensors/anomalies            # Get detected anomalies

# ALERTS
GET    /alerts/active                # Get active alerts
GET    /alerts/history               # Alert history
POST   /alerts/{alert_id}/acknowledge # Acknowledge alert
GET    /alerts/{alert_id}            # Get alert details

# INCIDENTS
GET    /incidents                    # List incidents
POST   /incidents                    # Create incident
GET    /incidents/{incident_id}      # Get incident details
PUT    /incidents/{incident_id}      # Update incident
POST   /incidents/{incident_id}/rca  # Root cause analysis
GET    /incidents/similar/{incident_id} # Find similar incidents

# PERMITS
GET    /permits/active               # Active permits
GET    /permits                      # All permits
POST   /permits                      # Create permit
GET    /permits/{permit_id}          # Get permit details
PUT    /permits/{permit_id}          # Update permit
DELETE /permits/{permit_id}          # Revoke permit

# EQUIPMENT & MAINTENANCE
GET    /equipment                    # List equipment
GET    /equipment/{equipment_id}     # Equipment details
GET    /equipment/{equipment_id}/health # Equipment health score
GET    /maintenance/schedule         # Maintenance schedule
POST   /maintenance/record           # Record maintenance
GET    /maintenance/{equipment_id}   # Equipment maintenance history

# WORKERS & SHIFTS
GET    /workers                      # List workers
GET    /workers/{worker_id}          # Worker details
GET    /workers/{worker_id}/location # Worker current location
POST   /shifts                       # Create shift
GET    /shifts/active                # Active shifts
GET    /shifts/{shift_id}            # Shift details

# GEOSPATIAL
GET    /geospatial/plant-map         # Plant layout map
GET    /geospatial/heatmap           # Risk heatmap
GET    /geospatial/zones             # Zone information
GET    /geospatial/zones/{zone_id}/risk # Zone risk score
POST   /geospatial/evacuation-plan   # Generate evacuation plan

# EMERGENCY RESPONSE
POST   /emergency/evacuate           # Trigger evacuation
POST   /emergency/{incident_id}/all-clear # All-clear signal
GET    /emergency/{incident_id}/status # Emergency status
GET    /emergency/evacuation-plan/{incident_id} # Evacuation details

# COMPLIANCE & REPORTING
GET    /compliance/status            # Compliance status
GET    /compliance/gaps              # Compliance gaps
POST   /compliance/audit             # Trigger compliance audit
GET    /reports/incident/{incident_id} # Incident report
GET    /reports/regulatory/{incident_id} # Regulatory report
GET    /reports/dashboard            # Dashboard report

# KNOWLEDGE GRAPH & RAG
POST   /knowledge/query              # Query knowledge graph
GET    /guidance/similar-incidents   # Similar incidents guidance
POST   /guidance/regulations         # Regulatory guidance
POST   /guidance/ask                 # Ask safety copilot

# ANALYTICS & DASHBOARD
GET    /dashboard/overview           # Dashboard overview
GET    /dashboard/kpis               # Key performance indicators
GET    /analytics/trends             # Safety trends
GET    /analytics/patterns           # Safety pattern analysis
GET    /analytics/predictions        # Future predictions

# SETTINGS & ADMIN
GET    /settings/system              # System settings
PUT    /settings/system              # Update settings
POST   /settings/calibration         # Sensor calibration
GET    /audit-logs                   # Audit logs
GET    /system/health                # System health status
```

---

## FRONTEND-BACKEND INTEGRATION

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    FRONTEND-BACKEND INTEGRATION                       │
└──────────────────────────────────────────────────────────────────────┘

FRONTEND (Web Dashboard / Mobile App)
  │
  ├─ REST API Calls (HTTP)
  │  └─> GET /api/v1/risk/current
  │  └─> POST /api/v1/alerts/acknowledge
  │  └─> GET /api/v1/dashboard/overview
  │
  ├─ WebSocket (Real-time updates)
  │  └─> ws://api.example.com/ws/dashboard
  │  └─> Subscribe to: risk-updates, alert-events, sensor-data
  │
  └─ File Uploads
     └─> POST /api/v1/files/upload (for incident attachments)

     ↓↓↓ (API Gateway + Authentication)

API GATEWAY (FastAPI + Kong)
  │
  ├─ JWT Token Validation
  ├─ Rate Limiting
  ├─ Request Routing
  └─ CORS Handling

     ↓↓↓

MICROSERVICES LAYER
  │
  ├─ Risk Prediction Service
  ├─ Vision Intelligence Service
  ├─ Sensor Intelligence Service
  ├─ Compliance Service
  ├─ Emergency Response Service
  └─ Geospatial Service

     ↓↓↓

DATA LAYER
  │
  ├─ PostgreSQL (Structured)
  ├─ InfluxDB (Time-Series)
  ├─ Neo4j (Knowledge Graph)
  ├─ MongoDB (Documents)
  └─ Redis (Cache)

     ↓↓↓

MESSAGE QUEUE (Kafka)
  │
  ├─ sensor-events
  ├─ alert-events
  ├─ incident-events
  └─ emergency-events

     ↓↓↓ (Back to Frontend via WebSocket)

REAL-TIME UPDATES
  └─ Risk score changes
  └─ Alert notifications
  └─ Incident updates
  └─ Sensor anomalies
```

### Request-Response Cycle Example

```
1. User View Dashboard
   ├─ Frontend: GET /api/v1/dashboard/overview
   ├─ Backend: Fetch from Redis (cached)
   ├─ If not cached: Aggregate from services
   └─ Response: { risk_score: 45, alerts: [...], sensors: [...] }

2. Sensor Data Arrives
   ├─ IoT Device: Publish to Kafka topic "sensor-events"
   ├─ Stream Processor: Consume from Kafka
   ├─ Stream Processor: Aggregate + Publish to "sensor-aggregated"
   ├─ Risk Service: Consume aggregated data
   ├─ Risk Service: Calculate risk score
   ├─ Risk Service: If high risk, publish to "alert-events"
   ├─ Notification Service: Send alerts
   └─ WebSocket: Push to connected clients

3. User Takes Action (Acknowledge Alert)
   ├─ Frontend: POST /api/v1/alerts/{alert_id}/acknowledge
   ├─ Backend: Update alert status in PostgreSQL
   ├─ Backend: Publish to "alert-acknowledged" Kafka topic
   ├─ Backend: Update Redis cache
   └─ Response: { status: 'acknowledged', timestamp: ... }

4. Real-Time Dashboard Update
   ├─ WebSocket Server: Receive alert-acknowledged event
   ├─ WebSocket Server: Broadcast to all connected clients
   ├─ Frontend: Receive WebSocket message
   ├─ Frontend: Update Redux state
   ├─ Frontend: Re-render dashboard components
   └─ User See: Alert removed/marked as acknowledged
```

---

## TECHNOLOGY STACK

### Backend Stack
```yaml
Languages & Frameworks:
  - Python 3.11+
    - FastAPI (async API framework)
    - Celery (async task processing)
    - SQLAlchemy (ORM)
  - Node.js 18+ (for some microservices)
    - Express (REST API)

Databases:
  - PostgreSQL 15+ (relational data)
  - InfluxDB 2.x (time-series data)
  - Neo4j 5.x (knowledge graphs)
  - MongoDB 7.x (documents)
  - Redis 7.x (caching/sessions)

Message Queue:
  - Apache Kafka 3.x (event streaming)
  - RabbitMQ (alternative for queuing)

ML/AI:
  - TensorFlow 2.13+
  - PyTorch 2.x
  - Scikit-learn 1.3+
  - XGBoost 2.x
  - LightGBM 4.x
  - Ultralytics YOLO v8
  - FastAPI + ONNX Runtime (model serving)
  - LangChain (LLM integration)
  - Pinecone/FAISS (vector DB for RAG)

Graph & Knowledge:
  - Neo4j Python Driver
  - py2neo (Neo4j ORM)

Monitoring & Logging:
  - Prometheus (metrics)
  - Grafana (visualization)
  - ELK Stack (logs)
  - Jaeger (distributed tracing)

Containerization & Orchestration:
  - Docker (containerization)
  - Kubernetes (orchestration)
  - Helm (K8s package manager)

Infrastructure:
  - AWS / GCP / Azure
  - Cloud Storage (S3/GCS)
  - Docker Registry
  - CI/CD (GitHub Actions / GitLab CI)
```

### Frontend Stack
```yaml
Web Dashboard:
  - React 18+
  - TypeScript 5.x
  - Redux Toolkit (state management)
  - Redux Thunk/Saga (side effects)
  - Axios (HTTP client)
  - Socket.io-client (WebSocket)
  
Styling:
  - Tailwind CSS 3.x
  - styled-components
  - Material-UI or Ant Design

Visualization:
  - Recharts (charts)
  - Chart.js (advanced charts)
  - Mapbox GL (geospatial)
  - Three.js (3D digital twin)
  - D3.js (custom visualizations)

Real-time:
  - Socket.io (WebSocket)
  - React Query (data fetching)

Build & Dev Tools:
  - Vite (build tool)
  - ESLint (linting)
  - Prettier (formatting)
  - Jest (testing)
  - Cypress (E2E testing)

Mobile:
  - React Native or Flutter
  - Redux for state management
  - React Query for data
  - Firebase for push notifications

Deployment:
  - Vercel / Netlify (static hosting)
  - Docker (containerization)
  - Kubernetes (orchestration)
```

---

## FEATURE SPECIFICATIONS

### Feature 1: Compound Risk Detection Engine

**Objective:** Detect dangerous combinations of conditions that no single sensor would flag.

**Technical Specification:**
```python
# Compound Risk Scoring
risk_score = (
    gas_reading * gas_weight(0.40) +
    maintenance_active * maintenance_weight(0.25) +
    worker_count_normalized * worker_weight(0.20) +
    permit_type_risk * permit_weight(0.15)
)

# Trigger Conditions
- If gas_reading > 100 ppm AND maintenance_active: Alert
- If gas_reading > 100 ppm AND worker_count > 0: Alert
- If gas_reading > 100 ppm AND hot_work_permit_active: CRITICAL ALERT
- If maintenance_active AND shift_change_happening: Alert
- If multiple conditions above 0.5 weight sum: COMPOUND RISK DETECTED
```

**API Endpoint:**
```
POST /api/v1/risk/compound/{zone_id}
Request: {
  "gas_level": 120,
  "maintenance_active": true,
  "worker_count": 5,
  "permit_type": "HOT_WORK",
  "permit_active": true
}
Response: {
  "compound_risk_score": 0.82,
  "risk_level": "CRITICAL",
  "contributing_factors": [
    "gas_level",
    "maintenance_active",
    "hot_work_permit_active"
  ]
}
```

---

### Feature 2: Real-time Geospatial Safety Heatmap

**Objective:** Visualize risk zones dynamically as conditions change.

**Components:**
- Plant map overlay
- Risk zone coloring (red/orange/yellow/green)
- Worker locations
- Hazard locations
- Restricted zone boundaries

**Technology:** Mapbox GL + React

---

### Feature 3: Vision Intelligence (PPE Detection & Fall Detection)

**Objective:** Detect safety violations from CCTV feeds.

**Models:** YOLOv8 + Pose Estimation

**Detections:**
- Missing helmet
- Missing safety vest
- Worker in restricted zone
- Fire/smoke detection
- Fall detection
- Crowding detection

---

### Feature 4: Incident Pattern Intelligence (RAG)

**Objective:** Find similar incidents and regulatory guidance.

**Components:**
- Document ingestion (incidents, regulations)
- Vector embeddings (OpenAI/Hugging Face)
- Semantic search (FAISS/Pinecone)
- RAG pipeline with citations

---

### Feature 5: Emergency Response Orchestrator

**Objective:** Autonomous emergency response workflow.

**Workflow:**
1. Detect critical risk
2. Calculate evacuation routes
3. Assign response teams
4. Generate incident report
5. Send notifications
6. Track all-clear signal

---

### Feature 6: Digital Twin

**Objective:** 3D real-time visualization of plant.

**Technology:** Three.js + React

**Elements:**
- Equipment 3D models
- Sensor readings displayed
- Worker positions
- Risk zones highlighted
- Real-time updates

---

## IMPLEMENTATION ROADMAP

### Week 1: Foundation & Setup
- [ ] Project setup (repo, environments, Docker)
- [ ] Database schemas (PostgreSQL, InfluxDB, Neo4j, MongoDB)
- [ ] API Gateway & authentication
- [ ] Basic sensor data ingestion pipeline
- [ ] Kafka topics setup
- [ ] Redux store structure
- [ ] Basic dashboard components

**Deliverables:** Working dev environment, basic API endpoints, sample data flowing

### Week 2: Core Intelligence & Models
- [ ] YOLO model fine-tuning for safety detection
- [ ] XGBoost risk prediction model training
- [ ] LSTM forecasting model
- [ ] Anomaly detection (Isolation Forest)
- [ ] Knowledge Graph population
- [ ] RAG pipeline for compliance
- [ ] Vision Intelligence Service
- [ ] Risk Prediction Service

**Deliverables:** All ML models trained, inference endpoints working

### Week 3: System Integration & Agents
- [ ] Multi-agent system implementation
- [ ] Agent orchestration (Supervisor)
- [ ] Emergency Response Service
- [ ] Geospatial Service
- [ ] Notification Service (SMS, email, push)
- [ ] WebSocket real-time updates
- [ ] Dashboard components (Heatmap, Alerts, Digital Twin)
- [ ] Mobile app screens

**Deliverables:** Agents working, emergency flow tested, real-time updates flowing

### Week 4: Polish, Testing & Deployment
- [ ] Comprehensive testing (unit, integration, E2E)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring & logging setup
- [ ] Documentation
- [ ] Demo video creation
- [ ] Presentation deck
- [ ] Docker deployment
- [ ] Kubernetes manifests

**Deliverables:** Production-ready deployment, full documentation, demo video

---

## DEPLOYMENT ARCHITECTURE

### Local Development Setup
```bash
# Using Docker Compose
docker-compose up

# Services:
# - FastAPI Backend: http://localhost:8000
# - React Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
# - InfluxDB: http://localhost:8086
# - Neo4j: http://localhost:7687
# - Redis: localhost:6379
# - Kafka: localhost:9092
# - Elasticsearch: http://localhost:9200
# - Kibana: http://localhost:5601
```

### Production Deployment (Kubernetes)
```yaml
# Kubernetes Architecture
Ingress (nginx-ingress)
  │
  ├─ Backend Services (pods)
  │  ├─ API Gateway (3 replicas)
  │  ├─ Vision Service (2 replicas)
  │  ├─ Risk Service (3 replicas)
  │  ├─ Geospatial Service (2 replicas)
  │  └─ ... (other services)
  │
  ├─ Frontend (SPA)
  │  └─ React app served by nginx
  │
  └─ Databases (StatefulSets)
     ├─ PostgreSQL (primary + replicas)
     ├─ InfluxDB
     ├─ Neo4j
     └─ Redis

Monitoring Stack:
  ├─ Prometheus (metrics scraping)
  ├─ Grafana (dashboards)
  ├─ Elasticsearch (logs)
  ├─ Kibana (log visualization)
  └─ Jaeger (distributed tracing)

CI/CD Pipeline:
  ├─ GitHub Actions
  ├─ Build & Push Docker images
  ├─ Run tests
  ├─ Deploy to staging
  ├─ Run E2E tests
  └─ Deploy to production
```

---

## SECURITY CONSIDERATIONS

### Authentication & Authorization
- JWT tokens (refresh + access tokens)
- Role-Based Access Control (RBAC)
- Multi-factor authentication option
- Rate limiting on all endpoints
- CORS configuration

### Data Security
- Encryption at rest (database, storage)
- Encryption in transit (HTTPS, TLS)
- API key management (Vault)
- Audit logging for all operations
- PII data masking in logs

### Infrastructure Security
- Network policies (Kubernetes)
- Pod security policies
- Image scanning (vulnerability)
- Secrets management (K8s secrets)
- Regular security audits

---

## MONITORING & OBSERVABILITY

### Metrics
- System uptime
- API response times
- Model inference latency
- Data pipeline lag
- Alert response time
- Emergency response time

### Logging
- Structured JSON logs
- Centralized logging (ELK)
- Log retention policies
- Alert on error rates

### Tracing
- Distributed tracing (Jaeger)
- Request flow visualization
- Performance bottleneck identification

---

## TEAM STRUCTURE & RESPONSIBILITIES

```
Team Lead / Project Manager (1)
├─ Overall timeline & deliverables
└─ Stakeholder communication

Backend Team (4)
├─ API Development (1)
├─ ML Model Integration (2)
└─ Database & Infrastructure (1)

Frontend Team (2)
├─ Web Dashboard (1)
└─ Mobile App (1)

ML/AI Team (2)
├─ Computer Vision Models (1)
└─ Prediction & Forecasting Models (1)

DevOps & Infrastructure (1)
├─ Docker & Kubernetes
├─ CI/CD pipelines
└─ Monitoring & logging setup
```

---

## NEXT STEPS

1. **Environment Setup**
   - Clone repository
   - Install dependencies
   - Configure .env files
   - Run docker-compose

2. **Database Initialization**
   - Create PostgreSQL schemas
   - Initialize InfluxDB buckets
   - Load Neo4j graph
   - Seed initial data

3. **Model Preparation**
   - Download pre-trained YOLO
   - Train/fine-tune models with sample data
   - Create model serving endpoints
   - Set up model versioning

4. **API Development**
   - Implement core endpoints
   - Set up authentication
   - Create data models (Pydantic)
   - Implement error handling

5. **Frontend Development**
   - Create component structure
   - Implement Redux store
   - Connect to APIs
   - Build Heatmap & Alert components

6. **Integration**
   - Connect frontend to backend
   - Implement WebSocket communication
   - Test end-to-end flows
   - Performance optimization

7. **Testing**
   - Unit tests for services
   - Integration tests
   - E2E tests
   - Load testing

8. **Deployment**
   - Containerize services
   - Create Kubernetes manifests
   - Set up CI/CD
   - Deploy to cluster

---

## APPENDIX: QUICK REFERENCE

### Key Data Structures
- Sensor Reading: `{sensor_id, value, unit, status, timestamp}`
- Risk Score: `{risk_score, risk_level, affecting_factors[]}`
- Incident: `{incident_id, type, location, severity, timestamp}`
- Alert: `{alert_id, type, severity, affected_zones[], timestamp}`
- Permit: `{permit_id, type, status, workers[], duration}`

### Key Algorithms
- Risk Calculation: Weighted sum of factors
- Anomaly Detection: Isolation Forest
- Forecasting: LSTM with confidence intervals
- Compound Risk: Multi-factor correlation
- Path Planning: Dijkstra's algorithm (evacuation routes)

### Key Integration Points
- Kafka: Sensor data → Risk calculation
- WebSocket: Backend changes → Frontend updates
- Neo4j: Entity relationships → Risk reasoning
- RAG: Document corpus → Guidance & compliance

---

**Document Version:** 1.0
**Last Updated:** June 2025
**Status:** Complete Architecture Ready for Implementation

