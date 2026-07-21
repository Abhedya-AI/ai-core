import { apiClient } from './client';
import { WorkPermit } from '../../types';
import { MOCK_PERMITS } from '../../constants/dummyData';

export const permitsApi = {
  getPermits: async (): Promise<WorkPermit[]> => {
    await apiClient.get('/permits');
    return MOCK_PERMITS;
  },

  create: async (permit: Omit<WorkPermit, 'id' | 'permitNumber' | 'status'>): Promise<WorkPermit> => {
    await apiClient.post('/permits', { body: permit });
    return {
      ...permit,
      id: `pmt-${Math.floor(Math.random() * 1000) + 3000}`,
      permitNumber: `WP-2026-${Math.floor(Math.random() * 9000) + 1000}`,
      status: 'PENDING',
    };
  },

  approve: async (id: string, approverName: string): Promise<WorkPermit> => {
    await apiClient.post(`/permits/${id}/approve`, { body: { approverName } });
    const permit = MOCK_PERMITS.find((p) => p.id === id);
    if (!permit) throw new Error('Permit not found');
    return {
      ...permit,
      status: 'APPROVED',
      approver: approverName,
      validFrom: new Date().toISOString(),
    };
  },

  revoke: async (id: string): Promise<WorkPermit> => {
    await apiClient.post(`/permits/${id}/revoke`);
    const permit = MOCK_PERMITS.find((p) => p.id === id);
    if (!permit) throw new Error('Permit not found');
    return {
      ...permit,
      status: 'REVOKED',
    };
  },
};
