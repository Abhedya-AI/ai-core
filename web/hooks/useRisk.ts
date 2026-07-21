import { useQuery } from '@tanstack/react-query';
import { riskApi } from '../services/api/risk';

export function useRisk() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['plant_risk_assessment'],
    queryFn: () => riskApi.getAssessment(),
    refetchInterval: 10000, // Poll every 10 seconds
  });

  return {
    assessment: data || {
      overallScore: 0,
      criticalSectorsCount: 0,
      mitigationActive: false,
      sectors: [],
    },
    isLoading,
    error,
    refresh: refetch,
  };
}
