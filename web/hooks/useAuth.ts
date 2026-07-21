import { useAuthStore } from '../store/useAuthStore';

export function useAuth() {
  const { user, isAuthenticated, isTwoFactorRequired, isLoading, error, login, verifyTwoFactor, logout, clearError, hasPermission } = useAuthStore();

  return {
    user,
    isAuthenticated,
    isTwoFactorRequired,
    isLoading,
    error,
    login,
    verifyTwoFactor,
    logout,
    clearError,
    hasPermission,
  };
}
