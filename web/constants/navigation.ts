import { ROUTES } from './routes';

export interface NavItem {
  title: string;
  href: string;
  iconName: string;
  badge?: {
    text: string;
    variant: 'info' | 'warning' | 'danger' | 'critical' | 'success' | 'accent';
  };
  children?: NavItem[];
  permission?: string;
  isPinned?: boolean;
}

export interface NavCategory {
  category: string;
  items: NavItem[];
}

export const NAVIGATION_ITEMS: NavCategory[] = [
  {
    category: 'Core Monitoring',
    items: [
      {
        title: 'Mission Control',
        href: ROUTES.dashboard.home,
        iconName: 'LayoutDashboard',
      },
      {
        title: 'Digital Twin',
        href: ROUTES.dashboard.digitalTwin,
        iconName: 'Cpu',
        badge: { text: '3D Live', variant: 'accent' },
      },
      {
        title: 'Knowledge Graph',
        href: ROUTES.dashboard.knowledgeGraph,
        iconName: 'Network',
      },
    ],
  },
  {
    category: 'Telemetry & Safety',
    items: [
      {
        title: 'Sensor Grid',
        href: ROUTES.dashboard.sensors,
        iconName: 'Radio',
        badge: { text: '1,492', variant: 'info' },
      },
      {
        title: 'Live Alerts',
        href: ROUTES.dashboard.alerts,
        iconName: 'BellRing',
        badge: { text: '8 Active', variant: 'danger' },
      },
      {
        title: 'Personnel Tracking',
        href: ROUTES.dashboard.workers,
        iconName: 'Users',
      },
    ],
  },
  {
    category: 'Operations',
    items: [
      {
        title: 'Work Permits',
        href: ROUTES.dashboard.permits,
        iconName: 'FileSpreadsheet',
        badge: { text: '12 Active', variant: 'success' },
      },
      {
        title: 'Maintenance',
        href: ROUTES.dashboard.maintenance,
        iconName: 'Wrench',
      },
      {
        title: 'Compliance Logs',
        href: ROUTES.dashboard.compliance,
        iconName: 'ShieldCheck',
      },
    ],
  },
  {
    category: 'Analysis & Config',
    items: [
      {
        title: 'Analytics & Trends',
        href: ROUTES.dashboard.analytics,
        iconName: 'BarChart3',
      },
      {
        title: 'Safety Reports',
        href: ROUTES.dashboard.reports,
        iconName: 'FileText',
      },
      {
        title: 'Settings Panel',
        href: ROUTES.dashboard.settings,
        iconName: 'Settings',
      },
    ],
  },
  {
    category: 'Emergency Dispatch',
    items: [
      {
        title: 'Emergency Control',
        href: ROUTES.dashboard.emergency,
        iconName: 'ShieldAlert',
        badge: { text: 'SYS OK', variant: 'success' },
      },
    ],
  },
];
