import { useAlertsStore } from '../store/useAlertsStore';

export function useAlerts() {
  const { alerts, activeCount, criticalCount, setAlerts, addAlert, acknowledgeAlert, resolveAlert } = useAlertsStore();

  return {
    alerts,
    activeCount,
    criticalCount,
    setAlerts,
    addAlert,
    acknowledgeAlert,
    resolveAlert,
  };
}
