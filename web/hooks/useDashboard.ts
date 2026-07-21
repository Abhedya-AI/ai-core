import { useDashboardStore } from '../store/useDashboardStore';

export function useDashboard() {
  const { timeRange, layoutMode, isSidebarExpanded, selectedSector, setTimeRange, setLayoutMode, setSidebarExpanded, setSelectedSector } = useDashboardStore();

  return {
    timeRange,
    layoutMode,
    isSidebarExpanded,
    selectedSector,
    setTimeRange,
    setLayoutMode,
    setSidebarExpanded,
    setSelectedSector,
  };
}
