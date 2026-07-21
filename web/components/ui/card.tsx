import * as React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  borderAccent?: 'primary' | 'success' | 'warning' | 'danger' | 'critical' | 'accent' | 'none';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverEffect = false, borderAccent = 'none', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={twMerge(
          clsx(
            'bg-card text-text-primary rounded-xl border transition-all duration-150',
            {
              'border-border': borderAccent === 'none',
              'border-primary/50': borderAccent === 'primary',
              'border-success/50': borderAccent === 'success',
              'border-warning/50': borderAccent === 'warning',
              'border-danger/50': borderAccent === 'danger',
              'border-critical/70 glow-critical': borderAccent === 'critical',
              'border-accent/50': borderAccent === 'accent',
              'hover:border-border/80 hover:bg-card/90': hoverEffect && borderAccent === 'none',
              'hover:border-primary': hoverEffect && borderAccent === 'primary',
              'hover:border-success': hoverEffect && borderAccent === 'success',
              'hover:border-warning': hoverEffect && borderAccent === 'warning',
              'hover:border-danger': hoverEffect && borderAccent === 'danger',
              'hover:border-accent': hoverEffect && borderAccent === 'accent',
            },
            className
          )
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

export const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={twMerge('flex flex-col space-y-1.5 p-4 border-b border-border/30', className)} {...props} />
);

export const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={twMerge('text-sm font-semibold tracking-tight uppercase text-text-primary', className)} {...props} />
);

export const CardDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={twMerge('text-xs text-muted font-normal', className)} {...props} />
);

export const CardContent = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={twMerge('p-4', className)} {...props} />
);

export const CardFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={twMerge('flex items-center p-4 border-t border-border/30 bg-background/20', className)} {...props} />
);

// KPI Card
interface KpiCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  unit?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  status?: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE';
  subtitle?: string;
}

export const KpiCard = ({ title, value, unit, trend, status = 'NORMAL', subtitle, className, ...props }: KpiCardProps) => {
  const getStatusColor = () => {
    switch (status) {
      case 'WARNING':
        return 'warning';
      case 'CRITICAL':
        return 'critical';
      case 'OFFLINE':
        return 'none';
      default:
        return 'success';
    }
  };

  return (
    <Card borderAccent={getStatusColor()} className={twMerge('relative overflow-hidden', className)} {...props}>
      <CardContent className="flex flex-col justify-between h-full space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-wider uppercase text-muted">{title}</span>
          {status !== 'NORMAL' && (
            <span className={clsx(
              'px-1.5 py-0.5 text-[10px] font-bold rounded-sm border uppercase',
              {
                'border-warning text-warning bg-warning/10': status === 'WARNING',
                'border-critical text-critical bg-critical/10': status === 'CRITICAL',
                'border-border text-muted bg-border/20': status === 'OFFLINE',
              }
            )}>
              {status}
            </span>
          )}
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-3xl font-mono font-bold tracking-tight text-text-primary">{value}</span>
          {unit && <span className="text-sm font-semibold text-text-secondary">{unit}</span>}
        </div>
        <div className="flex items-center justify-between text-[11px]">
          {trend ? (
            <span className={clsx(
              'font-semibold flex items-center gap-1',
              {
                'text-success': trend.direction === 'up',
                'text-danger': trend.direction === 'down',
                'text-text-secondary': trend.direction === 'neutral',
              }
            )}>
              {trend.direction === 'up' ? '▲' : trend.direction === 'down' ? '▼' : '■'} {trend.value}%
            </span>
          ) : (
            <span className="text-muted">{subtitle || 'Live Feed'}</span>
          )}
          <span className="text-[10px] font-mono text-muted/80">SECURE CHANNEL</span>
        </div>
      </CardContent>
    </Card>
  );
};

// Metric Card
interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  status?: 'NORMAL' | 'WARNING' | 'CRITICAL';
}

export const MetricCard = ({ label, value, min, max, unit, status = 'NORMAL', className, ...props }: MetricCardProps) => {
  const percent = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  
  return (
    <Card className={twMerge('bg-card', className)} {...props}>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-text-secondary uppercase">{label}</span>
          <span className={clsx(
            'text-xs font-mono font-bold',
            {
              'text-success': status === 'NORMAL',
              'text-warning': status === 'WARNING',
              'text-danger': status === 'CRITICAL',
            }
          )}>
            {value} {unit}
          </span>
        </div>
        <div className="h-1.5 w-full bg-border/50 rounded-xl overflow-hidden">
          <div
            style={{ width: `${percent}%` }}
            className={clsx(
              'h-full transition-all duration-300',
              {
                'bg-success': status === 'NORMAL',
                'bg-warning': status === 'WARNING',
                'bg-danger': status === 'CRITICAL',
              }
            )}
          />
        </div>
        <div className="flex justify-between text-[9px] font-mono text-muted">
          <span>MIN: {min} {unit}</span>
          <span>MAX: {max} {unit}</span>
        </div>
      </CardContent>
    </Card>
  );
};
