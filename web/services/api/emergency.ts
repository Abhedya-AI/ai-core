import { apiClient } from './client';

export interface EmergencyState {
  isActive: boolean;
  alertId?: string;
  triggeredBy?: string;
  triggeredAt?: string;
  isolationValvesClosed: boolean;
  ventilationOverrideActive: boolean;
}

export const emergencyApi = {
  trigger: async (alertId: string, operatorId: string): Promise<EmergencyState> => {
    await apiClient.post('/emergency/trigger', { body: { alertId, operatorId } });
    return {
      isActive: true,
      alertId,
      triggeredBy: operatorId,
      triggeredAt: new Date().toISOString(),
      isolationValvesClosed: true,
      ventilationOverrideActive: true,
    };
  },

  clear: async (operatorId: string): Promise<EmergencyState> => {
    await apiClient.post('/emergency/clear', { body: { operatorId } });
    return {
      isActive: false,
      isolationValvesClosed: false,
      ventilationOverrideActive: false,
    };
  },
};
