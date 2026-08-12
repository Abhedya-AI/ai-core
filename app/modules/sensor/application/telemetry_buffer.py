from collections import deque
from typing import List
from app.modules.sensor.domain.models import SensorReading
from app.core.logging import get_logger

log = get_logger("app.modules.sensor.application.telemetry_buffer")

class TelemetryBuffer:
    """In-memory circular buffer for recent readings per sensor."""

    def __init__(self, max_readings_per_sensor: int = 200):
        """
        Initialize with configurable buffer size.
        
        Args:
            max_readings_per_sensor: Max number of readings to store per sensor.
        """
        self.max_readings_per_sensor = max_readings_per_sensor
        self._buffers: dict[str, deque[SensorReading]] = {}

    def push(self, reading: SensorReading) -> None:
        """
        Add a reading to the sensor's buffer.
        
        Args:
            reading: The sensor reading to add.
        """
        if not reading.sensor_id:
            return
            
        if reading.sensor_id not in self._buffers:
            self._buffers[reading.sensor_id] = deque(maxlen=self.max_readings_per_sensor)
            
        self._buffers[reading.sensor_id].append(reading)

    def get_recent(self, sensor_id: str, count: int = 50) -> List[SensorReading]:
        """
        Get N most recent readings.
        
        Args:
            sensor_id: The ID of the sensor.
            count: Number of readings to retrieve.
            
        Returns:
            list[SensorReading]: List of recent readings.
        """
        if sensor_id not in self._buffers:
            return []
            
        buffer = self._buffers[sensor_id]
        return list(buffer)[-count:]

    def get_values(self, sensor_id: str, count: int = 50) -> List[float]:
        """
        Get just the float values for math operations.
        
        Args:
            sensor_id: The ID of the sensor.
            count: Number of values to retrieve.
            
        Returns:
            list[float]: List of recent float values.
        """
        readings = self.get_recent(sensor_id, count)
        return [r.value for r in readings]

    def get_all_sensor_ids(self) -> List[str]:
        """
        List all sensors with buffered data.
        
        Returns:
            list[str]: List of sensor IDs.
        """
        return list(self._buffers.keys())

    def clear(self, sensor_id: str) -> None:
        """
        Clear buffer for a sensor.
        
        Args:
            sensor_id: The ID of the sensor.
        """
        if sensor_id in self._buffers:
            del self._buffers[sensor_id]
