import { apiClient } from './client';

export interface AnalyticsTrendPoint {
  timestamp: string;
  safetyIndex: number;
  emissions: number;
  downtimeMinutes: number;
}

export const analyticsApi = {
  getTrends: async (range: string): Promise<AnalyticsTrendPoint[]> => {
    await apiClient.get('/analytics/trends', { params: { range } });
    return [
      { timestamp: '08:00', safetyIndex: 98.2, emissions: 4.2, downtimeMinutes: 0 },
      { timestamp: '10:00', safetyIndex: 98.4, emissions: 3.8, downtimeMinutes: 0 },
      { timestamp: '12:00', safetyIndex: 94.1, emissions: 8.5, downtimeMinutes: 15 },
      { timestamp: '14:00', safetyIndex: 95.8, emissions: 6.1, downtimeMinutes: 0 },
      { timestamp: '16:00', safetyIndex: 97.0, emissions: 4.8, downtimeMinutes: 0 },
    ];
  },
};
