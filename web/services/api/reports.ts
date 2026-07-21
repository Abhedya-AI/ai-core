import { apiClient } from './client';

export interface SafetyReport {
  id: string;
  title: string;
  date: string;
  author: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED';
  summary: string;
}

export const reportsApi = {
  getReports: async (): Promise<SafetyReport[]> => {
    await apiClient.get('/reports');
    return [
      { id: 'rep-001', title: 'Weekly H2S Compliance Assessment', date: '2026-07-14', author: 'Devin Vance', status: 'APPROVED', summary: 'Summary of emissions checks in sulfur lines' },
      { id: 'rep-002', title: 'Hydrocracker Valve Incident Report', date: '2026-07-18', author: 'Elena Rostova', status: 'SUBMITTED', summary: 'Incident logging after pressure overflow' },
    ];
  },
};
