import { create } from 'zustand';
import { MOCK_KNOWLEDGE_GRAPH } from '../constants/dummyData';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  status: string;
}

interface GraphLink {
  source: string;
  target: string;
  relation: string;
}

interface KnowledgeGraphState {
  nodes: GraphNode[];
  links: GraphLink[];
  selectedNodeId: string | null;
  searchQuery: string;
  focusedTypes: string[];
  setGraph: (nodes: GraphNode[], links: GraphLink[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  toggleTypeFilter: (type: string) => void;
}

export const useKnowledgeGraphStore = create<KnowledgeGraphState>((set) => ({
  nodes: MOCK_KNOWLEDGE_GRAPH.nodes,
  links: MOCK_KNOWLEDGE_GRAPH.links,
  selectedNodeId: null,
  searchQuery: '',
  focusedTypes: [],

  setGraph: (nodes, links) => set({ nodes, links }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),

  toggleTypeFilter: (type) =>
    set((state) => ({
      focusedTypes: state.focusedTypes.includes(type)
        ? state.focusedTypes.filter((t) => t !== type)
        : [...state.focusedTypes, type],
    })),
}));
