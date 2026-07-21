import { apiClient } from './client';

export interface ComplianceStandard {
  id: string;
  code: string;
  name: string;
  status: 'COMPLIANT' | 'PENDING_REVIEW' | 'NON_COMPLIANT';
  lastChecked: string;
}

export const complianceApi = {
  getStandards: async (): Promise<ComplianceStandard[]> => {
    await apiClient.get('/compliance/standards');
    return [
      { id: 'std-osha-01', code: 'OSHA 1910.119', name: 'Process Safety Management of Highly Hazardous Chemicals', status: 'COMPLIANT', lastChecked: new Date().toISOString() },
      { id: 'std-epa-02', code: 'EPA Title V', name: 'Clean Air Act Operating Permit Emissions Thresholds', status: 'COMPLIANT', lastChecked: new Date().toISOString() },
      { id: 'std-api-570', code: 'API 570', name: 'Piping Inspection Code: In-service Inspection, Rating, Repair', status: 'PENDING_REVIEW', lastChecked: new Date(Date.now() - 86400000).toISOString() },
    ];
  },
};
