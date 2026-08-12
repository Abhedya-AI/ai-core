from typing import Callable, Optional
from app.modules.sensor.domain.models import SensorReading
from app.modules.knowledge.domain.enums import SensorType
from app.core.logging import get_logger

log = get_logger("app.modules.sensor.application.normalizer")

class UnitNormalizer:
    """Normalizes sensor reading units to canonical units."""

    _CANONICAL_UNITS: dict[str, str] = {
        SensorType.TEMPERATURE.value: "°C",
        SensorType.PRESSURE.value: "bar",
        SensorType.GAS.value: "ppm",
        SensorType.VIBRATION.value: "mm/s",
        SensorType.ACOUSTIC.value: "dB",
        SensorType.HUMIDITY.value: "%RH",
        SensorType.AIR_QUALITY.value: "AQI",
        SensorType.FLOW.value: "L/min",
        SensorType.SMOKE.value: "%obs",
    }

    _CONVERSION_TABLE: dict[tuple[str, str], Callable[[float], float]] = {
        ("°F", "°C"): lambda f: (f - 32) * 5.0 / 9.0,
        ("F", "°C"): lambda f: (f - 32) * 5.0 / 9.0,
        ("F", "C"): lambda f: (f - 32) * 5.0 / 9.0,
        ("PSI", "bar"): lambda p: p * 0.0689476,
        ("kPa", "bar"): lambda p: p * 0.01,
        ("ppm", "mg/m³"): lambda p: p * 1.2,
        ("in", "mm"): lambda i: i * 25.4,
        ("ft", "m"): lambda f: f * 0.3048,
    }

    def normalize_reading(self, reading: SensorReading, target_unit: Optional[str] = None) -> SensorReading:
        """
        Converts to canonical unit and returns new immutable reading.
        
        Args:
            reading: The sensor reading to normalize.
            target_unit: The target unit to convert to. If None, auto-infer from unit or conversion table.
            
        Returns:
            SensorReading: A new instance of SensorReading with updated value and unit.
        """
        if target_unit is None:
            # Auto-infer target unit for F, PSI, kPa if present
            if reading.unit in ("F", "°F"):
                target_unit = "°C"
            elif reading.unit == "PSI":
                target_unit = "bar"
            elif reading.unit == "kPa":
                target_unit = "bar"
            else:
                target_unit = reading.unit
            
        if reading.unit == target_unit or target_unit is None:
            return reading
            
        conversion_key = (reading.unit, target_unit)
        if conversion_key in self._CONVERSION_TABLE:
            new_value = self._CONVERSION_TABLE[conversion_key](reading.value)
            return reading.model_copy(update={"value": round(new_value, 4), "unit": target_unit})
            
        log.warning(f"No conversion found from {reading.unit} to {target_unit}")
        return reading

    def normalize(self, reading: SensorReading, target_unit: Optional[str] = None) -> SensorReading:
        """Alias for normalize_reading."""
        return self.normalize_reading(reading, target_unit=target_unit)

    def get_canonical_unit(self, sensor_type_str: str) -> str:
        """Returns the canonical unit for each SensorType."""
        return self._CANONICAL_UNITS.get(sensor_type_str, "unknown")
