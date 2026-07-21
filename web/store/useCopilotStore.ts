import { create } from 'zustand';
import { CopilotMessage } from '../types';
import { MOCK_COPILOT_MESSAGES } from '../constants/dummyData';

interface CopilotState {
  messages: CopilotMessage[];
  isThinking: boolean;
  isOpen: boolean;
  addMessage: (message: Omit<CopilotMessage, 'id' | 'timestamp'>) => void;
  setThinking: (isThinking: boolean) => void;
  setOpen: (isOpen: boolean) => void;
  clearHistory: () => void;
}

export const useCopilotStore = create<CopilotState>((set) => ({
  messages: MOCK_COPILOT_MESSAGES,
  isThinking: false,
  isOpen: false,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `msg-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  setThinking: (isThinking) => set({ isThinking }),
  setOpen: (isOpen) => set({ isOpen }),
  clearHistory: () => set({ messages: [] }),
}));
