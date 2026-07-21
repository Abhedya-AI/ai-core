import { UserRole } from '../types';

export interface RoleInfo {
  role: UserRole;
  label: string;
  description: string;
  badgeColor: string;
  accessLevel: number;
}

export const ROLES: Record<UserRole, RoleInfo> = {
  SYSTEM_ADMIN: {
    role: 'SYSTEM_ADMIN',
    label: 'System Administrator',
    description: 'Full administrative control over all plant settings, user permissions, and audit logs.',
    badgeColor: 'border-primary text-primary bg-primary/10',
    accessLevel: 10,
  },
  SAFETY_SUPERVISOR: {
    role: 'SAFETY_SUPERVISOR',
    label: 'Safety Supervisor',
    description: 'Manages work permits, evaluates plant risk scores, and manages active safety emergencies.',
    badgeColor: 'border-warning text-warning bg-warning/10',
    accessLevel: 8,
  },
  PLANT_OPERATOR: {
    role: 'PLANT_OPERATOR',
    label: 'Plant Operator',
    description: 'Monitors real-time sensor feeds, reports hazards, and raises emergency alerts.',
    badgeColor: 'border-success text-success bg-success/10',
    accessLevel: 5,
  },
  MAINTENANCE_TECH: {
    role: 'MAINTENANCE_TECH',
    label: 'Maintenance Technician',
    description: 'Diagnoses equipment issues, calibrates sensors, and updates work order logs.',
    badgeColor: 'border-accent text-accent bg-accent/10',
    accessLevel: 4,
  },
  DISPATCHER: {
    role: 'DISPATCHER',
    label: 'Dispatcher',
    description: 'Coordinates active shift schedules and dispatches emergency response units.',
    badgeColor: 'border-muted text-text-secondary bg-muted/10',
    accessLevel: 3,
  },
};
