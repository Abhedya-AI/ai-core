import { create } from 'zustand';
import { Worker } from '../types';
import { MOCK_WORKERS } from '../constants/dummyData';

interface WorkersState {
  workers: Worker[];
  selectedWorkerId: string | null;
  setWorkers: (workers: Worker[]) => void;
  setSelectedWorkerId: (id: string | null) => void;
  updateWorkerBiometrics: (id: string, heartRate: number, oxygenLevel: number, temp: number) => void;
  setWorkerStatus: (id: string, status: Worker['status']) => void;
}

export const useWorkersStore = create<WorkersState>((set, get) => ({
  workers: MOCK_WORKERS,
  selectedWorkerId: null,

  setWorkers: (workers) => set({ workers }),
  setSelectedWorkerId: (selectedWorkerId) => set({ selectedWorkerId }),

  updateWorkerBiometrics: (id, heartRate, oxygenLevel, bodyTemperature) => {
    const updated = get().workers.map((w) => {
      if (w.id === id) {
        let status = w.status;
        // Raise safety alert if vitals are compromised
        if (heartRate > 120 || oxygenLevel < 93 || bodyTemperature > 38.5) {
          status = 'HAZARD_ALERT';
        }

        return {
          ...w,
          heartRate,
          oxygenLevel,
          bodyTemperature,
          status,
          lastActive: new Date().toISOString(),
        };
      }
      return w;
    });
    set({ workers: updated });
  },

  setWorkerStatus: (id, status) => {
    const updated = get().workers.map((w) =>
      w.id === id
        ? {
            ...w,
            status,
            lastActive: new Date().toISOString(),
          }
        : w
    );
    set({ workers: updated });
  },
}));
