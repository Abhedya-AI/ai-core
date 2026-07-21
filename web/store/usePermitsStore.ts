import { create } from 'zustand';
import { WorkPermit } from '../types';
import { MOCK_PERMITS } from '../constants/dummyData';

interface PermitsState {
  permits: WorkPermit[];
  setPermits: (permits: WorkPermit[]) => void;
  createPermit: (permit: Omit<WorkPermit, 'id' | 'permitNumber' | 'status'>) => void;
  approvePermit: (id: string, approverName: string) => void;
  revokePermit: (id: string) => void;
  completePermit: (id: string) => void;
}

export const usePermitsStore = create<PermitsState>((set, get) => ({
  permits: MOCK_PERMITS,

  setPermits: (permits) => set({ permits }),

  createPermit: (newPermit) => {
    const permitNumber = `WP-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const id = `pmt-${Math.floor(3000 + Math.random() * 1000)}`;
    const permit: WorkPermit = {
      ...newPermit,
      id,
      permitNumber,
      status: 'PENDING',
    };
    set({ permits: [...get().permits, permit] });
  },

  approvePermit: (id, approverName) => {
    const updated = get().permits.map((p) =>
      p.id === id
        ? {
            ...p,
            status: 'APPROVED' as const,
            approver: approverName,
            validFrom: new Date().toISOString(),
          }
        : p
    );
    set({ permits: updated });
  },

  revokePermit: (id) => {
    const updated = get().permits.map((p) =>
      p.id === id ? { ...p, status: 'REVOKED' as const } : p
    );
    set({ permits: updated });
  },

  completePermit: (id) => {
    const updated = get().permits.map((p) =>
      p.id === id ? { ...p, status: 'COMPLETED' as const } : p
    );
    set({ permits: updated });
  },
}));
