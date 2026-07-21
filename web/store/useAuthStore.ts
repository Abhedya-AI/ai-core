import { create } from 'zustand';
import { User } from '../types';
import { MOCK_USER } from '../constants/dummyData';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isTwoFactorRequired: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  verifyTwoFactor: (code: string) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isTwoFactorRequired: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    // Simulate API request delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    if (email === 'admin@abhedya.ai' || email === 'd.vance@abhedya.ai') {
      // Mock successful login requiring 2FA
      set({ isTwoFactorRequired: true, isLoading: false });
      return true;
    } else {
      set({ error: 'Invalid credentials. Access Denied.', isLoading: false });
      return false;
    }
  },

  verifyTwoFactor: async (code) => {
    set({ isLoading: true, error: null });
    await new Promise((resolve) => setTimeout(resolve, 800));

    if (code === '123456' || code === '000000') {
      set({
        user: MOCK_USER,
        isAuthenticated: true,
        isTwoFactorRequired: false,
        isLoading: false,
      });
      return true;
    } else {
      set({ error: 'Invalid 2FA token. Verification Failed.', isLoading: false });
      return false;
    }
  },

  logout: () => {
    set({ user: null, isAuthenticated: false, isTwoFactorRequired: false, error: null });
  },

  clearError: () => set({ error: null }),

  hasPermission: (permission) => {
    const user = get().user;
    if (!user) return false;
    return user.permissions.includes(permission);
  },
}));
