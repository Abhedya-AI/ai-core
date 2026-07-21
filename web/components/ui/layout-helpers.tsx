import * as React from 'react';
import { twMerge } from 'tailwind-merge';
import { Breadcrumb, BreadcrumbItem } from './navigation';

// Page Header
interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
}

export const PageHeader = ({ title, subtitle, breadcrumbs, actions, className, ...props }: PageHeaderProps) => {
  return (
    <div className={twMerge('flex flex-col gap-2 pb-4 border-b border-border/30 mb-6', className)} {...props}>
      {breadcrumbs && <Breadcrumb items={breadcrumbs} className="mb-1" />}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary uppercase font-sans">{title}</h1>
          {subtitle && <p className="text-xs text-muted mt-0.5 leading-relaxed">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
      </div>
    </div>
  );
};

// Section Header
interface SectionHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  actions?: React.ReactNode;
}

export const SectionHeader = ({ title, actions, className, ...props }: SectionHeaderProps) => {
  return (
    <div className={twMerge('flex items-center justify-between py-2 border-b border-border/20 mb-4', className)} {...props}>
      <h2 className="text-xs font-bold tracking-wider uppercase text-text-secondary font-mono">{title}</h2>
      {actions && <div className="flex items-center gap-1.5">{actions}</div>}
    </div>
  );
};

// Toolbar
export const Toolbar = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={twMerge('flex items-center justify-between gap-4 bg-card/40 border border-border p-2 rounded-xl mb-4', className)} {...props}>
      {children}
    </div>
  );
};

// Filter Bar
export const FilterBar = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={twMerge('flex items-center gap-2 flex-wrap', className)} {...props}>
      {children}
    </div>
  );
};
