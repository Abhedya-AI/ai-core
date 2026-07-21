import { create } from 'zustand';
import { Alert } from '../types';
import { MOCK_ALERTS } from '../constants/dummyData';

interface AlertsState {
  alerts: Alert[];
  activeCount: number;
  criticalCount: number;
  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  acknowledgeAlert: (id: string, userId: string) => void;
  resolveAlert: (id: string) => void;
}

export const useAlertsStore = create<AlertsState>((set, get) => {
  const recalculateCounts = (alerts: Alert[]) => {
    const active = alerts.filter((a) => a.status !== 'RESOLVED');
    return {
      activeCount: active.length,
      criticalCount: active.filter((a) => a.severity === 'CRITICAL' || a.severity === 'DANGER').length,
    };
  };

  const initialCounts = recalculateCounts(MOCK_ALERTS);

  return {
    alerts: MOCK_ALERTS,
    ...initialCounts,

    setAlerts: (alerts) => {
      const counts = recalculateCounts(alerts);
      set({ alerts, ...counts });
    },

    addAlert: (alert) => {
      const updated = [alert, ...get().alerts];
      set({ alerts: updated, ...recalculateCounts(updated) });
    },

    acknowledgeAlert: (id, userId) => {
      const updated = get().alerts.map((a) =>
        a.id === id
          ? {
              ...a,
              status: 'ACKNOWLEDGED' as const,
              acknowledgedAt: new Date().toISOString(),
              assignedTo: userId,
            }
          : a
      );
      set({ alerts: updated, ...recalculateCounts(updated) });
    },

    resolveAlert: (id) => {
      const updated = get().alerts.map((a) =>
        a.id === id
          ? {
              ...a,
              status: 'RESOLVED' as const,
              resolvedAt: new Date().toISOString(),
            }
          : a
      );
      set({ alerts: updated, ...recalculateCounts(updated) });
    },
  };
});
