import { create } from 'zustand';

interface ThemeState {
  theme: 'dark'; // Enforce dark theme only
  isHighContrast: boolean;
  toggleHighContrast: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: 'dark',
  isHighContrast: false,
  toggleHighContrast: () => set((state) => ({ isHighContrast: !state.isHighContrast })),
}));
