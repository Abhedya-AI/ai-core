import { apiClient } from './client';

export interface DashboardStats {
  plantRiskScore: number; // 0-100
  activeAlertsCount: number;
  activePermitsCount: number;
  onlineSensorsCount: number;
  totalWorkersOnSite: number;
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    await apiClient.get('/dashboard/stats');
    return {
      plantRiskScore: 42.5,
      activeAlertsCount: 8,
      activePermitsCount: 12,
      onlineSensorsCount: 1484,
      totalWorkersOnSite: 28,
    };
  },
};
