import { apiClient } from './client';
import { Sensor } from '../../types';
import { MOCK_SENSORS } from '../../constants/dummyData';

export const sensorsApi = {
  getSensors: async (): Promise<Sensor[]> => {
    await apiClient.get('/sensors');
    return MOCK_SENSORS;
  },

  calibrate: async (id: string): Promise<{ success: boolean; calibrationDate: string }> => {
    await apiClient.post(`/sensors/${id}/calibrate`);
    return {
      success: true,
      calibrationDate: new Date().toISOString(),
    };
  },
};
