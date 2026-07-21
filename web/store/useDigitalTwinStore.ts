import { create } from 'zustand';
import { DigitalTwinNode } from '../types';

interface DigitalTwinState {
  nodes: DigitalTwinNode[];
  selectedNodeId: string | null;
  cameraPosition: [number, number, number];
  isOrbiting: boolean;
  activeLayer: 'THERMAL' | 'PRESSURE' | 'PIPING' | 'NORMAL';
  setNodes: (nodes: DigitalTwinNode[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setCameraPosition: (pos: [number, number, number]) => void;
  setOrbiting: (isOrbiting: boolean) => void;
  setActiveLayer: (layer: 'THERMAL' | 'PRESSURE' | 'PIPING' | 'NORMAL') => void;
}

export const useDigitalTwinStore = create<DigitalTwinState>((set) => ({
  nodes: [],
  selectedNodeId: null,
  cameraPosition: [0, 15, 30],
  isOrbiting: true,
  activeLayer: 'NORMAL',

  setNodes: (nodes) => set({ nodes }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  setCameraPosition: (cameraPosition) => set({ cameraPosition }),
  setOrbiting: (isOrbiting) => set({ isOrbiting }),
  setActiveLayer: (activeLayer) => set({ activeLayer }),
}));
