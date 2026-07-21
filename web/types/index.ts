export type UserRole = 'SYSTEM_ADMIN' | 'SAFETY_SUPERVISOR' | 'PLANT_OPERATOR' | 'MAINTENANCE_TECH' | 'DISPATCHER';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  permissions: string[];
  plantId: string;
}

export type AlertSeverity = 'INFO' | 'WARNING' | 'DANGER' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface Alert {
  id: string;
  timestamp: string;
  severity: AlertSeverity;
  status: AlertStatus;
  category: 'SAFETY' | 'SENSOR' | 'EQUIPMENT' | 'PROCESS' | 'SECURITY' | 'ENVIRONMENT';
  message: string;
  location: string;
  sensorId?: string;
  equipmentId?: string;
  assignedTo?: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
}

export type SensorType = 'TEMPERATURE' | 'PRESSURE' | 'GAS_LEAK' | 'VIBRATION' | 'HUMIDITY' | 'FLOW_RATE' | 'VOLTAGE';
export type SensorStatus = 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE';

export interface Sensor {
  id: string;
  name: string;
  type: SensorType;
  status: SensorStatus;
  value: number;
  unit: string;
  location: string;
  lastUpdated: string;
  historicalData: { timestamp: string; value: number }[];
  minThreshold: number;
  maxThreshold: number;
}

export interface Worker {
  id: string;
  name: string;
  status: 'ACTIVE' | 'ON_BREAK' | 'OFF_SHIFT' | 'HAZARD_ALERT';
  role: string;
  location: string;
  heartRate: number;
  oxygenLevel: number;
  bodyTemperature: number;
  lastActive: string;
  assignedTasks: string[];
}

export type PermitType = 'HOT_WORK' | 'CONFINED_SPACE' | 'HEIGHTS' | 'ELECTRICAL' | 'EXCAVATION' | 'CHEMICAL';
export type PermitStatus = 'PENDING' | 'APPROVED' | 'ACTIVE' | 'COMPLETED' | 'REVOKED' | 'EXPIRED';

export interface WorkPermit {
  id: string;
  permitNumber: string;
  title: string;
  type: PermitType;
  status: PermitStatus;
  description: string;
  location: string;
  applicant: string;
  approver?: string;
  validFrom: string;
  validTo: string;
  safetyPrecautions: string[];
  hazardsIdentified: string[];
}

export interface SystemNotification {
  id: string;
  timestamp: string;
  title: string;
  message: string;
  read: boolean;
  category: 'ALERT' | 'PERMIT' | 'SYSTEM' | 'MAINTENANCE';
}

export interface DigitalTwinNode {
  id: string;
  label: string;
  type: 'VESSEL' | 'PIPE' | 'VALVE' | 'PUMP' | 'COMPRESSOR';
  status: 'OPERATIONAL' | 'MAINTENANCE' | 'OFFLINE' | 'CRITICAL';
  telemetry: Record<string, number | string>;
  position: { x: number; y: number; z: number };
}

export interface CopilotMessage {
  id: string;
  sender: 'USER' | 'AI';
  content: string;
  timestamp: string;
  references?: { type: 'SENSOR' | 'PERMIT' | 'ALERT' | 'DOC'; id: string; name: string }[];
}

export interface PlantSettings {
  plantName: string;
  locationCode: string;
  refreshRateMs: number;
  notificationsEnabled: boolean;
  audioAlertsEnabled: boolean;
  twoFactorEnabled: boolean;
  debugMode: boolean;
}
