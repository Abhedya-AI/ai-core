from datetime import datetime, timedelta, timezone
import math
from app.modules.sensor.domain.models import SensorReading, IngestionBatch
from app.core.logging import get_logger

log = get_logger("app.modules.sensor.application.validators")

class ReadingValidator:
    """Validator for sensor readings."""

    def __init__(self) -> None:
        self._seen_keys: set[tuple[str, str]] = set()

    def validate_reading(self, reading: SensorReading) -> tuple[bool, list[str]]:
        """
        Validate a single sensor reading.
        
        Returns:
            tuple[bool, list[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        if not reading.sensor_id or reading.sensor_id.strip() == "":
            errors.append("Empty sensor_id")

        if any(c in reading.sensor_id for c in ("'", '"', ";", "--")):
            errors.append("Invalid characters in sensor_id")
            
        if math.isnan(reading.value) or math.isinf(reading.value):
            errors.append("Value is NaN or Infinity")
        elif not (-1000 <= reading.value <= 100000):
            errors.append(f"Value {reading.value} is out of bounds (-1000 to 100000)")
            
        if reading.quality_score is not None:
            if not (0.0 <= reading.quality_score <= 1.0):
                errors.append(f"Quality score {reading.quality_score} must be between 0.0 and 1.0")
                
        try:
            ts_dt = datetime.fromisoformat(reading.timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if ts_dt > now + timedelta(minutes=5):
                errors.append("Timestamp is more than 5 minutes in the future")
            if ts_dt < now - timedelta(hours=24):
                errors.append("Timestamp is more than 24 hours in the past")
        except Exception:
            errors.append("Invalid timestamp format")
            
        return len(errors) == 0, errors

    def validate(self, reading: SensorReading) -> tuple[bool, list[str]]:
        """Alias for validate_reading."""
        return self.validate_reading(reading)

    def is_duplicate(self, reading: SensorReading) -> bool:
        """Check if reading is a duplicate by (sensor_id, timestamp)."""
        key = (reading.sensor_id, reading.timestamp)
        if key in self._seen_keys:
            return True
        self._seen_keys.add(key)
        return False

    def validate_batch(self, batch: IngestionBatch) -> tuple[list[SensorReading], list[dict]]:
        """
        Validate a batch of readings.
        
        Returns:
            tuple[list[SensorReading], list[dict]]: (valid_readings, rejection_reports)
        """
        valid_readings = []
        rejection_reports = []
        
        for reading in batch.readings:
            is_valid, errors = self.validate_reading(reading)
            if is_valid:
                valid_readings.append(reading)
            else:
                rejection_reports.append({
                    "sensor_id": reading.sensor_id,
                    "timestamp": reading.timestamp,
                    "errors": errors
                })
                
        return valid_readings, rejection_reports

    def detect_duplicates(self, readings: list[SensorReading]) -> list[SensorReading]:
        """
        Deduplicate readings by (sensor_id, timestamp) tuple.
        
        Returns:
            list[SensorReading]: List of deduplicated readings.
        """
        seen = set()
        unique_readings = []
        
        for reading in readings:
            key = (reading.sensor_id, reading.timestamp)
            if key not in seen:
                seen.add(key)
                unique_readings.append(reading)
                
        return unique_readings
