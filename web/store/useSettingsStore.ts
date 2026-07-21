import { create } from 'zustand';
import { PlantSettings } from '../types';

interface SettingsState {
  settings: PlantSettings;
  updateSettings: (settings: Partial<PlantSettings>) => void;
  resetSettings: () => void;
}

const DEFAULT_SETTINGS: PlantSettings = {
  plantName: 'Baytown Hydrocracker Unit 04',
  locationCode: 'BAY-HC-04',
  refreshRateMs: 2000,
  notificationsEnabled: true,
  audioAlertsEnabled: false,
  twoFactorEnabled: true,
  debugMode: false,
};

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: DEFAULT_SETTINGS,

  updateSettings: (updatedFields) =>
    set((state) => ({
      settings: { ...state.settings, ...updatedFields },
    })),

  resetSettings: () => set({ settings: DEFAULT_SETTINGS }),
}));
