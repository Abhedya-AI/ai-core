import { create } from 'zustand';

export type TimeRange = '1H' | '6H' | '24H' | '7D' | '30D';
export type PlantLayoutMode = 'GRID' | 'SCHEMATIC' | 'COMPACT';

interface DashboardState {
  timeRange: TimeRange;
  layoutMode: PlantLayoutMode;
  isSidebarExpanded: boolean;
  selectedSector: string | null;
  setTimeRange: (range: TimeRange) => void;
  setLayoutMode: (mode: PlantLayoutMode) => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setSelectedSector: (sector: string | null) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  timeRange: '1H',
  layoutMode: 'GRID',
  isSidebarExpanded: true,
  selectedSector: null,

  setTimeRange: (timeRange) => set({ timeRange }),
  setLayoutMode: (layoutMode) => set({ layoutMode }),
  setSidebarExpanded: (isSidebarExpanded) => set({ isSidebarExpanded }),
  setSelectedSector: (selectedSector) => set({ selectedSector }),
}));
