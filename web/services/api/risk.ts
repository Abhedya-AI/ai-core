import { apiClient } from './client';

export interface PlantRiskAssessment {
  overallScore: number;
  criticalSectorsCount: number;
  mitigationActive: boolean;
  sectors: { name: string; score: number; hazardsCount: number }[];
}

export const riskApi = {
  getAssessment: async (): Promise<PlantRiskAssessment> => {
    await apiClient.get('/risk/assessment');
    return {
      overallScore: 42.5,
      criticalSectorsCount: 2,
      mitigationActive: false,
      sectors: [
        { name: 'Sector A - Hydrocracker', score: 24.5, hazardsCount: 0 },
        { name: 'Sector B - Compressor Deck', score: 58.0, hazardsCount: 1 },
        { name: 'Sector C - Sulfur Recovery', score: 82.2, hazardsCount: 2 },
        { name: 'Sector D - Storage Terminal', score: 12.0, hazardsCount: 0 },
      ],
    };
  },
};
