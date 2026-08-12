from __future__ import annotations

import time
import re
from typing import Any
import numpy as np

from app.core.logging import get_logger

try:
    from app.modules.platform.feature_store.feature_registry import FeatureDefinition, FeatureType
except ImportError:
    FeatureDefinition = None
    FeatureType = None

log = get_logger(__name__)

class FeatureValidator:
    async def validate_schema(self, feature_def: Any, value: Any) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        errors = []
        if value is None:
            return {"valid": True, "errors": []}
            
        ft = feature_def.feature_type
        
        if ft == "NUMERICAL" or ft.value == "NUMERICAL":
            if not isinstance(value, (int, float)):
                errors.append(f"Expected numerical value, got {type(value).__name__}")
        elif ft == "CATEGORICAL" or ft.value == "CATEGORICAL":
            if not isinstance(value, str):
                errors.append(f"Expected categorical string, got {type(value).__name__}")
        elif ft == "BOOLEAN" or ft.value == "BOOLEAN":
            if not isinstance(value, bool):
                errors.append(f"Expected boolean, got {type(value).__name__}")
        elif ft == "EMBEDDING" or ft.value == "EMBEDDING":
            if not isinstance(value, list) or not all(isinstance(v, (int, float)) for v in value):
                errors.append("Expected list of floats for embedding")
                
        latency = time.perf_counter() - t0
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    async def validate_range(self, feature_def: Any, value: float | str, validation_rules: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        violations = []
        
        if value is None:
            return {"valid": True, "violations": []}
            
        if isinstance(value, (int, float)):
            if "min" in validation_rules and value < validation_rules["min"]:
                violations.append(f"Value {value} below minimum {validation_rules['min']}")
            if "max" in validation_rules and value > validation_rules["max"]:
                violations.append(f"Value {value} above maximum {validation_rules['max']}")
                
        if isinstance(value, str):
            if "allowed_values" in validation_rules and value not in validation_rules["allowed_values"]:
                violations.append(f"Value {value} not in allowed_values")
            if "regex_pattern" in validation_rules:
                pattern = validation_rules["regex_pattern"]
                if not re.match(pattern, value):
                    violations.append(f"Value {value} does not match pattern {pattern}")
                    
        latency = time.perf_counter() - t0
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }

    async def validate_null_rate(self, feature_name: str, values: list[Any], max_null_rate: float = 0.1) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        total = len(values)
        if total == 0:
            return {"null_rate": 0.0, "valid": True, "null_count": 0, "total": 0}
            
        null_count = sum(1 for v in values if v is None)
        null_rate = null_count / total
        
        latency = time.perf_counter() - t0
        return {
            "null_rate": null_rate,
            "valid": null_rate <= max_null_rate,
            "null_count": null_count,
            "total": total
        }

    async def validate_distribution(
        self,
        feature_name: str,
        current_values: list[float],
        baseline_values: list[float],
        significance_level: float = 0.05
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        if not current_values or not baseline_values:
            return {"ks_statistic": 0.0, "drift_detected": False, "description": "Insufficient data"}
            
        cur_arr = np.sort(np.array([v for v in current_values if v is not None], dtype=float))
        base_arr = np.sort(np.array([v for v in baseline_values if v is not None], dtype=float))
        
        if len(cur_arr) == 0 or len(base_arr) == 0:
            return {"ks_statistic": 0.0, "drift_detected": False, "description": "No non-null data"}
            
        # Compute KS statistic manually for independence from scipy
        n1 = len(cur_arr)
        n2 = len(base_arr)
        
        data_all = np.concatenate([cur_arr, base_arr])
        cdf1 = np.searchsorted(cur_arr, data_all, side='right') / n1
        cdf2 = np.searchsorted(base_arr, data_all, side='right') / n2
        
        d_statistic = float(np.max(np.abs(cdf1 - cdf2)))
        
        # Approximate p-value threshold
        # critical_value approx = sqrt(-0.5 * ln(alpha)) * sqrt((n1 + n2) / (n1 * n2))
        en = np.sqrt((n1 * n2) / (n1 + n2))
        critical_value = np.sqrt(-0.5 * np.log(significance_level)) / en
        
        drift_detected = d_statistic > critical_value
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed KS for {feature_name} in {latency:.4f}s: D={d_statistic:.4f}")
        
        return {
            "ks_statistic": d_statistic,
            "drift_detected": drift_detected,
            "description": f"KS stat {d_statistic:.4f} vs critical {critical_value:.4f}"
        }

    async def validate_batch(self, feature_vectors: list[dict[str, Any]], feature_defs: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        valid_count = 0
        invalid_count = 0
        errors_by_feature = {}
        
        for vector in feature_vectors:
            vector_valid = True
            
            for fname, val in vector.items():
                if fname in feature_defs:
                    fdef = feature_defs[fname]
                    
                    # Schema check
                    schema_res = await self.validate_schema(fdef, val)
                    if not schema_res["valid"]:
                        vector_valid = False
                        if fname not in errors_by_feature:
                            errors_by_feature[fname] = []
                        errors_by_feature[fname].extend(schema_res["errors"])
                        
                    # Range check
                    range_res = await self.validate_range(fdef, val, fdef.validation_rules)
                    if not range_res["valid"]:
                        vector_valid = False
                        if fname not in errors_by_feature:
                            errors_by_feature[fname] = []
                        errors_by_feature[fname].extend(range_res["violations"])
                        
            if vector_valid:
                valid_count += 1
            else:
                invalid_count += 1
                
        latency = time.perf_counter() - t0
        return {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "errors_by_feature": errors_by_feature
        }

    async def validate_completeness(self, feature_vector: dict[str, Any], required_features: list[str]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        missing = []
        for req in required_features:
            if req not in feature_vector or feature_vector[req] is None:
                missing.append(req)
                
        complete = len(missing) == 0
        completeness_rate = 1.0 if not required_features else (len(required_features) - len(missing)) / len(required_features)
        
        latency = time.perf_counter() - t0
        return {
            "complete": complete,
            "missing_features": missing,
            "completeness_rate": completeness_rate
        }

_feature_validator_instance = None

def get_feature_validator() -> FeatureValidator:
    global _feature_validator_instance
    if _feature_validator_instance is None:
        _feature_validator_instance = FeatureValidator()
    return _feature_validator_instance
