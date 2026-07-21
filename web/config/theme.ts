export const THEME = {
  colors: {
    background: '#060B14',
    card: '#101827',
    border: '#22314D',
    primary: '#2563EB',
    success: '#22C55E',
    warning: '#F59E0B',
    danger: '#EF4444',
    critical: '#B91C1C',
    accent: '#38BDF8',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    muted: '#64748B',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '32px',
    '4xl': '48px',
    '5xl': '64px',
    '6xl': '96px',
  },
  radii: {
    xl: '12px',
  },
} as const;

export type ThemeColors = typeof THEME.colors;
export type ThemeSpacing = typeof THEME.spacing;
