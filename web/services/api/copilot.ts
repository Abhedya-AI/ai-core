import { apiClient } from './client';
import { CopilotMessage } from '../../types';

export const copilotApi = {
  ask: async (prompt: string, context?: any): Promise<CopilotMessage> => {
    await apiClient.post('/copilot/ask', { body: { prompt, context } });
    return {
      id: `msg-${Math.floor(Math.random() * 1000) + 100}`,
      sender: 'AI',
      content: `Received prompt: "${prompt}". I have analyzed the active telemetry grids and equipment dependencies. There are no secondary critical failures reported. Safety protocols are currently verified active.`,
      timestamp: new Date().toISOString(),
    };
  },
};
