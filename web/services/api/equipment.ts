import { apiClient } from './client';

export interface EquipmentItem {
  id: string;
  name: string;
  type: string;
  status: 'OPERATIONAL' | 'DEGRADED' | 'MAINTENANCE' | 'CRITICAL' | 'OFFLINE';
  lastService: string;
  efficiency: number;
}

export const equipmentApi = {
  getEquipment: async (): Promise<EquipmentItem[]> => {
    await apiClient.get('/equipment');
    return [
      { id: 'eq-hcr-02', name: 'Hydrocracker R-02 Vessel', type: 'REACTOR', status: 'OPERATIONAL', lastService: '2026-05-12', efficiency: 98.4 },
      { id: 'eq-cp-104', name: 'Reciprocating Compressor C-104', type: 'COMPRESSOR', status: 'DEGRADED', lastService: '2026-06-20', efficiency: 86.2 },
      { id: 'eq-f-101', name: 'Primary Heating Furnace F-101', type: 'FURNACE', status: 'OPERATIONAL', lastService: '2026-04-01', efficiency: 91.5 },
      { id: 'eq-p-203', name: 'Naphtha Feed Pump P-203', type: 'PUMP', status: 'OFFLINE', lastService: '2026-07-10', efficiency: 0 },
    ];
  },
};
