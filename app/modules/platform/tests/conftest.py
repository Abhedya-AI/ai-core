from __future__ import annotations
import pytest
from datetime import datetime, timezone
import uuid
import time
import asyncio

@pytest.fixture
def sample_model_version():
    return {
        "model_id": str(uuid.uuid4()),
        "name": "risk_predictor_v1",
        "description": "Test model",
        "version": "1.0.0",
        "module": "risk_prediction",
        "model_family": "ENSEMBLE",
        "stage": "DRAFT",
        "status": "TRAINED",
        "feature_names": ["temp", "pressure", "vibration"],
        "hyperparameters": {"n_estimators": 100, "max_depth": 5},
        "tags": ["production", "equipment"],
        "created_by": "test_user",
        "training_data_hash": "abc123",
        "deployment_config": {"replicas": 3},
        "lineage_parent_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

@pytest.fixture
def sample_tenant():
    return {
        "tenant_id": str(uuid.uuid4()),
        "name": "Test Plant Corp",
        "slug": "test-plant-corp",
        "tier": "PROFESSIONAL",
        "contact_email": "admin@testplant.com",
    }

@pytest.fixture
def sample_features():
    return {
        "temperature": 72.5,
        "pressure": 102.3,
        "vibration": 0.45,
        "humidity": 65.0,
        "noise_db": 80.0,
    }

@pytest.fixture
def baseline_data():
    import numpy as np
    np.random.seed(42)
    return list(np.random.normal(0.5, 0.1, 100))

@pytest.fixture
def current_data_no_drift(baseline_data):
    import numpy as np
    np.random.seed(123)
    return list(np.random.normal(0.51, 0.1, 100))

@pytest.fixture
def current_data_with_drift():
    import numpy as np
    np.random.seed(456)
    return list(np.random.normal(0.8, 0.15, 100))

@pytest.fixture
def sample_plant():
    return {
        "plant_id": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "name": "Plant Alpha",
        "location": "Mumbai, India",
        "plant_type": "CHEMICAL",
        "oee_score": 0.82,
        "safety_index": 0.91,
    }
