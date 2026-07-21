import { apiClient } from './client';
import { Alert } from '../../types';
import { MOCK_ALERTS } from '../../constants/dummyData';

export const alertsApi = {
  getAlerts: async (): Promise<Alert[]> => {
    await apiClient.get('/alerts');
    return MOCK_ALERTS;
  },

  acknowledge: async (id: string, userId: string): Promise<Alert> => {
    await apiClient.post(`/alerts/${id}/acknowledge`, { body: { userId } });
    const alert = MOCK_ALERTS.find((a) => a.id === id);
    if (!alert) throw new Error('Alert not found');
    return {
      ...alert,
      status: 'ACKNOWLEDGED',
      acknowledgedAt: new Date().toISOString(),
      assignedTo: userId,
    };
  },

  resolve: async (id: string): Promise<Alert> => {
    await apiClient.post(`/alerts/${id}/resolve`);
    const alert = MOCK_ALERTS.find((a) => a.id === id);
    if (!alert) throw new Error('Alert not found');
    return {
      ...alert,
      status: 'RESOLVED',
      resolvedAt: new Date().toISOString(),
    };
  },
};
