import { useSensorsStore } from '../store/useSensorsStore';

export function useSensors() {
  const { sensors, selectedSensorId, setSensors, setSelectedSensorId, updateSensorValue, setSensorStatus } = useSensorsStore();

  return {
    sensors,
    selectedSensorId,
    setSensors,
    setSelectedSensorId,
    updateSensorValue,
    setSensorStatus,
  };
}
