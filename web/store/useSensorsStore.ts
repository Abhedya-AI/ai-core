import { create } from 'zustand';
import { Sensor } from '../types';
import { MOCK_SENSORS } from '../constants/dummyData';

interface SensorsState {
  sensors: Sensor[];
  selectedSensorId: string | null;
  setSensors: (sensors: Sensor[]) => void;
  setSelectedSensorId: (id: string | null) => void;
  updateSensorValue: (id: string, value: number) => void;
  setSensorStatus: (id: string, status: Sensor['status']) => void;
}

export const useSensorsStore = create<SensorsState>((set, get) => ({
  sensors: MOCK_SENSORS,
  selectedSensorId: null,

  setSensors: (sensors) => set({ sensors }),
  setSelectedSensorId: (selectedSensorId) => set({ selectedSensorId }),

  updateSensorValue: (id, value) => {
    const updated = get().sensors.map((s) => {
      if (s.id === id) {
        const timestamp = new Date().toISOString();
        const historicalData = [...s.historicalData, { timestamp, value }].slice(-20); // Keep last 20 points
        
        // Auto check thresholds to determine status
        let status: Sensor['status'] = 'NORMAL';
        if (value >= s.maxThreshold || value <= s.minThreshold) {
          status = 'CRITICAL';
        } else if (value >= s.maxThreshold * 0.9 || value <= s.minThreshold * 1.1) {
          status = 'WARNING';
        }

        return {
          ...s,
          value,
          status,
          lastUpdated: timestamp,
          historicalData,
        };
      }
      return s;
    });
    set({ sensors: updated });
  },

  setSensorStatus: (id, status) => {
    const updated = get().sensors.map((s) =>
      s.id === id
        ? {
            ...s,
            status,
            lastUpdated: new Date().toISOString(),
          }
        : s
    );
    set({ sensors: updated });
  },
}));
