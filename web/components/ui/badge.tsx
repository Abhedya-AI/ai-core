import * as React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'danger' | 'critical' | 'muted';
}

export const Badge = ({ className, variant = 'secondary', children, ...props }: BadgeProps) => {
  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-semibold border font-mono tracking-wide uppercase',
          {
            'bg-primary/10 border-primary text-primary': variant === 'primary',
            'bg-border/20 border-border text-text-secondary': variant === 'secondary',
            'bg-accent/10 border-accent text-accent': variant === 'accent',
            'bg-success/10 border-success text-success': variant === 'success',
            'bg-warning/10 border-warning text-warning': variant === 'warning',
            'bg-danger/10 border-danger text-danger': variant === 'danger',
            'bg-critical/20 border-critical text-critical': variant === 'critical',
            'bg-muted/10 border-muted text-muted': variant === 'muted',
          },
          className
        )
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export interface PillProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger' | 'critical';
}

export const Pill = ({ className, variant = 'info', children, ...props }: PillProps) => {
  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center px-2.5 py-0.5 rounded-xl text-[11px] font-medium border uppercase tracking-wider',
          {
            'bg-primary/15 border-primary/30 text-accent': variant === 'info',
            'bg-success/15 border-success/30 text-success': variant === 'success',
            'bg-warning/15 border-warning/30 text-warning': variant === 'warning',
            'bg-danger/15 border-danger/30 text-danger': variant === 'danger',
            'bg-critical/25 border-critical/40 text-critical font-bold': variant === 'critical',
          },
          className
        )
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export interface StatusIndicatorProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: 'ONLINE' | 'OFFLINE' | 'WARNING' | 'CRITICAL' | 'STABLE';
  pulse?: boolean;
}

export const StatusIndicator = ({ status, pulse = true, className, ...props }: StatusIndicatorProps) => {
  const getColors = () => {
    switch (status) {
      case 'ONLINE':
      case 'STABLE':
        return 'bg-success border-success/30';
      case 'WARNING':
        return 'bg-warning border-warning/30';
      case 'CRITICAL':
        return 'bg-critical border-critical/30';
      default:
        return 'bg-muted border-muted/30';
    }
  };

  return (
    <span className={twMerge('inline-flex items-center gap-1.5 text-xs font-mono font-medium', className)} {...props}>
      <span className="relative flex h-2 w-2">
        {pulse && status !== 'OFFLINE' && (
          <span className={clsx(
            'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
            status === 'CRITICAL' ? 'bg-critical' : status === 'WARNING' ? 'bg-warning' : 'bg-success'
          )} />
        )}
        <span className={clsx('relative inline-flex rounded-full h-2 w-2 border', getColors())} />
      </span>
      <span className="text-[10px] uppercase text-text-secondary tracking-wider">{status}</span>
    </span>
  );
};

export interface AlertBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  count: number;
}

export const AlertBadge = ({ count, className, ...props }: AlertBadgeProps) => {
  if (count <= 0) return null;
  return (
    <span
      className={twMerge(
        'inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-sm text-[10px] font-bold font-mono',
        'bg-critical border border-critical text-text-primary glow-critical animate-pulse',
        className
      )}
      {...props}
    >
      {count}
    </span>
  );
};
