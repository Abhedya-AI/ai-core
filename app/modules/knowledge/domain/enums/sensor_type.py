from enum import Enum


class SensorType(str, Enum):
    """Types of industrial telemetry and observation devices."""

    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    GAS = "GAS"
    VIBRATION = "VIBRATION"
    ACOUSTIC = "ACOUSTIC"
    HUMIDITY = "HUMIDITY"
    AIR_QUALITY = "AIR_QUALITY"
    CAMERA = "CAMERA"
    FLOW = "FLOW"
    SMOKE = "SMOKE"
