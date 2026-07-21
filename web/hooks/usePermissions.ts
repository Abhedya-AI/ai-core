import { useAuthStore } from '../store/useAuthStore';
import { ROLE_PERMISSIONS } from '../constants/permissions';

export function usePermissions() {
  const { user } = useAuthStore();

  const can = (permission: string): boolean => {
    if (!user) return false;
    // Admin override
    if (user.role === 'SYSTEM_ADMIN') return true;
    
    // Check specific user permissions
    if (user.permissions.includes(permission)) return true;

    // Check fallback permissions associated with the role
    const rolePerms = ROLE_PERMISSIONS[user.role] || [];
    return rolePerms.includes(permission);
  };

  return {
    can,
    role: user?.role || null,
  };
}
