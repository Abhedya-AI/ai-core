import * as React from 'react';
import { ChevronRight } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

// Breadcrumb
export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export const Breadcrumb = ({ items, className }: BreadcrumbProps) => {
  return (
    <nav className={twMerge('flex items-center space-x-1.5 text-xs text-muted font-mono uppercase tracking-wider', className)}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <React.Fragment key={index}>
            {index > 0 && <ChevronRight size={12} className="text-muted/65" />}
            {isLast ? (
              <span className="text-text-primary font-semibold">{item.label}</span>
            ) : item.href ? (
              <a href={item.href} className="hover:text-text-primary transition-colors">
                {item.label}
              </a>
            ) : (
              <span>{item.label}</span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

// Tabs
export interface TabOption {
  id: string;
  label: string;
  count?: number;
}

export interface TabsProps {
  tabs: TabOption[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs = ({ tabs, activeTab, onChange, className }: TabsProps) => {
  return (
    <div className={twMerge('flex items-center border-b border-border/30 gap-1 bg-background/25 p-1 rounded-xl w-fit', className)}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'relative px-3 py-1.5 text-xs font-semibold uppercase tracking-wider font-sans select-none rounded-xl transition-all outline-none',
              isActive ? 'text-text-primary' : 'text-muted hover:text-text-secondary'
            )}
          >
            {isActive && (
              <motion.div
                layoutId="activeTabGlow"
                className="absolute inset-0 bg-border/40 rounded-xl -z-10"
                transition={{ duration: 0.15 }}
              />
            )}
            <span className="flex items-center gap-1.5">
              {tab.label}
              {tab.count !== undefined && (
                <span className={clsx(
                  'px-1 py-0.2 text-[9px] font-bold font-mono rounded',
                  isActive ? 'bg-primary text-text-primary' : 'bg-border/30 text-muted'
                )}>
                  {tab.count}
                </span>
              )}
            </span>
          </button>
        );
      })}
    </div>
  );
};

// Avatar
export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  status?: 'ONLINE' | 'OFFLINE' | 'WARNING' | 'CRITICAL';
}

export const Avatar = ({ src, name, size = 'md', status, className, ...props }: AvatarProps) => {
  const getInitials = (n: string) => {
    return n
      .split(' ')
      .map((p) => p[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  const getStatusColor = () => {
    switch (status) {
      case 'ONLINE':
        return 'bg-success';
      case 'WARNING':
        return 'bg-warning';
      case 'CRITICAL':
        return 'bg-critical';
      default:
        return 'bg-muted';
    }
  };

  const dimensions = {
    'w-6 h-6 text-[10px]': size === 'sm',
    'w-8 h-8 text-xs': size === 'md',
    'w-10 h-10 text-sm': size === 'lg',
  };

  return (
    <div className={twMerge('relative flex-shrink-0', className)} {...props}>
      <div className={twMerge(
        'rounded-xl border border-border bg-border/30 flex items-center justify-center font-bold font-mono text-text-secondary overflow-hidden select-none',
        clsx(dimensions)
      )}>
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={name} className="w-full h-full object-cover" />
        ) : (
          getInitials(name)
        )}
      </div>
      {status && (
        <span className={twMerge(
          'absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full border border-card',
          getStatusColor()
        )} />
      )}
    </div>
  );
};
