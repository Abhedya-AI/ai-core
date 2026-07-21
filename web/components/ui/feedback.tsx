import * as React from 'react';
import { twMerge } from 'tailwind-merge';
import { ShieldAlert, RefreshCw, FolderOpen } from 'lucide-react';

// Progress component
export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  indicatorClassName?: string;
}

export const Progress = ({ value, max = 100, className, indicatorClassName, ...props }: ProgressProps) => {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={twMerge('h-2 w-full bg-border/40 rounded-xl overflow-hidden', className)} {...props}>
      <div
        className={twMerge('h-full bg-primary transition-all duration-300', indicatorClassName)}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
};

// EmptyState component
export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  actionButton?: React.ReactNode;
}

export const EmptyState = ({ title, description, actionButton, className, ...props }: EmptyStateProps) => {
  return (
    <div
      className={twMerge(
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-border bg-card/25',
        className
      )}
      {...props}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-border/20 text-muted mb-4">
        <FolderOpen size={20} />
      </div>
      <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wide">{title}</h3>
      <p className="text-xs text-muted max-w-xs mt-1.5 mb-4 leading-relaxed">{description}</p>
      {actionButton}
    </div>
  );
};

// LoadingState component
export interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  message?: string;
  skeletonLayout?: boolean;
}

export const LoadingState = ({ message = 'Awaiting telemetry telemetry synchronization...', skeletonLayout = false, className, ...props }: LoadingStateProps) => {
  if (skeletonLayout) {
    return (
      <div className={twMerge('space-y-3 animate-pulse p-4', className)} {...props}>
        <div className="h-4 bg-border/40 rounded w-1/3" />
        <div className="h-10 bg-border/30 rounded" />
        <div className="h-10 bg-border/30 rounded w-5/6" />
      </div>
    );
  }

  return (
    <div className={twMerge('flex flex-col items-center justify-center p-8 space-y-3', className)} {...props}>
      <RefreshCw className="animate-spin text-accent" size={24} />
      <span className="text-xs font-mono font-semibold tracking-wider text-text-secondary uppercase">{message}</span>
    </div>
  );
};

// ErrorState component
export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState = ({ title = 'Data Feed Connection Error', message, onRetry, className, ...props }: ErrorStateProps) => {
  return (
    <div
      className={twMerge(
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-danger/20 bg-danger/5',
        className
      )}
      {...props}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-danger/10 text-danger mb-4">
        <ShieldAlert size={20} />
      </div>
      <h3 className="text-sm font-semibold text-danger uppercase tracking-wide">{title}</h3>
      <p className="text-xs text-muted max-w-sm mt-1.5 mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-card border border-danger/30 text-text-primary hover:bg-danger/10 transition-colors"
        >
          Retry Connection
        </button>
      )}
    </div>
  );
};
