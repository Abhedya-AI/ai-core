import { apiClient } from './client';
import { User } from '../../types';
import { MOCK_USER } from '../../constants/dummyData';

export const authApi = {
  login: async (email: string, password: string): Promise<{ success: boolean; requires2Fa: boolean }> => {
    await apiClient.post('/auth/login', { body: { email, password } });
    if (email === 'admin@abhedya.ai' || email === 'd.vance@abhedya.ai') {
      return { success: true, requires2Fa: true };
    }
    throw new Error('Invalid email or password');
  },

  verify2Fa: async (code: string): Promise<{ token: string; user: User }> => {
    await apiClient.post('/auth/2fa', { body: { code } });
    if (code === '123456' || code === '000000') {
      return {
        token: 'mock-jwt-token-9428',
        user: MOCK_USER,
      };
    }
    throw new Error('Verification code incorrect');
  },

  forgotPassword: async (email: string): Promise<{ success: boolean }> => {
    await apiClient.post('/auth/forgot-password', { body: { email } });
    return { success: true };
  },

  resetPassword: async (token: string, password: string): Promise<{ success: boolean }> => {
    await apiClient.post('/auth/reset-password', { body: { token, password } });
    return { success: true };
  },

  logout: async (): Promise<{ success: boolean }> => {
    await apiClient.post('/auth/logout');
    return { success: true };
  },
};
