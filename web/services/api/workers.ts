import { apiClient } from './client';
import { Worker } from '../../types';
import { MOCK_WORKERS } from '../../constants/dummyData';

export const workersApi = {
  getWorkers: async (): Promise<Worker[]> => {
    await apiClient.get('/workers');
    return MOCK_WORKERS;
  },

  getWorkerById: async (id: string): Promise<Worker> => {
    await apiClient.get(`/workers/${id}`);
    const worker = MOCK_WORKERS.find((w) => w.id === id);
    if (!worker) throw new Error('Worker not found');
    return worker;
  },
};
