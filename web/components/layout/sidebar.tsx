'use client';

import * as React from 'react';
import { clsx } from 'clsx';
import { usePathname } from 'next/navigation';
import { useDashboardStore } from '../../store/useDashboardStore';
import { useAuthStore } from '../../store/useAuthStore';
import { useAlertsStore } from '../../store/useAlertsStore';
import { usePermitsStore } from '../../store/usePermitsStore';
import { NAVIGATION_ITEMS, NavItem } from '../../constants/navigation';
import { Badge } from '../ui/badge';
import {
  LayoutDashboard,
  Cpu,
  Network,
  Radio,
  BellRing,
  Users,
  FileSpreadsheet,
  Wrench,
  ShieldCheck,
  BarChart3,
  FileText,
  Settings,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Search,
  LogOut,
  Power
} from 'lucide-react';

const IconMap: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  LayoutDashboard,
  Cpu,
  Network,
  Radio,
  BellRing,
  Users,
  FileSpreadsheet,
  Wrench,
  ShieldCheck,
  BarChart3,
  FileText,
  Settings,
  ShieldAlert,
};

export function Sidebar() {
  const pathname = usePathname();
  const { isSidebarExpanded, setSidebarExpanded } = useDashboardStore();
  const { user, logout } = useAuthStore();
  const { activeCount } = useAlertsStore();
  const { permits } = usePermitsStore();
  
  const [filterQuery, setFilterQuery] = React.useState('');

  const activePermitsCount = React.useMemo(() => {
    return permits.filter((p) => p.status === 'ACTIVE').length;
  }, [permits]);

  // Dynamic Badge replacement
  const getBadgeInfo = (item: NavItem) => {
    if (item.iconName === 'BellRing' && activeCount > 0) {
      return { text: `${activeCount} ACT`, variant: 'danger' as const };
    }
    if (item.iconName === 'FileSpreadsheet' && activePermitsCount > 0) {
      return { text: `${activePermitsCount} ACT`, variant: 'success' as const };
    }
    return item.badge;
  };

  return (
    <aside
      className={clsx(
        'h-screen sticky top-0 bg-card border-r border-border flex flex-col transition-all duration-200 z-40 select-none',
        isSidebarExpanded ? 'w-64' : 'w-16'
      )}
    >
      {/* Brand Logo Header */}
      <div className="h-14 border-b border-border/30 flex items-center justify-between px-4">
        {isSidebarExpanded ? (
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center font-bold text-xs text-text-primary glow-primary font-mono border border-primary/50">
              Ω
            </div>
            <span className="font-bold font-sans text-xs tracking-wider uppercase bg-gradient-to-r from-text-primary to-text-secondary bg-clip-text text-transparent">
              ABHEDYA AI
            </span>
          </div>
        ) : (
          <div className="h-6 w-6 rounded bg-primary mx-auto flex items-center justify-center font-bold text-xs text-text-primary glow-primary font-mono border border-primary/50">
            Ω
          </div>
        )}

        {isSidebarExpanded && (
          <button
            onClick={() => setSidebarExpanded(false)}
            className="text-muted hover:text-text-primary p-1 rounded hover:bg-border/20 transition-all focus:outline-none"
          >
            <ChevronLeft size={14} />
          </button>
        )}
      </div>

      {/* Expand trigger when collapsed */}
      {!isSidebarExpanded && (
        <div className="flex justify-center py-2 border-b border-border/10">
          <button
            onClick={() => setSidebarExpanded(true)}
            className="text-muted hover:text-text-primary p-1 rounded hover:bg-border/20 transition-all focus:outline-none"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Search Input Filter */}
      {isSidebarExpanded && (
        <div className="px-3 py-2 border-b border-border/10 flex items-center gap-2 text-muted focus-within:text-text-primary transition-colors">
          <Search size={12} className="flex-shrink-0" />
          <input
            type="text"
            placeholder="Filter operations modules..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="bg-transparent border-none text-[11px] font-sans w-full focus:outline-none focus:ring-0 placeholder-muted/75"
          />
        </div>
      )}

      {/* Navigation List Items */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-4 space-y-4">
        {NAVIGATION_ITEMS.map((cat) => {
          // Filter items based on query
          const filteredItems = cat.items.filter((item) =>
            item.title.toLowerCase().includes(filterQuery.toLowerCase())
          );

          if (filteredItems.length === 0) return null;

          return (
            <div key={cat.category} className="space-y-1.5">
              {isSidebarExpanded && (
                <span className="text-[9px] font-mono font-bold tracking-widest text-muted uppercase block px-2">
                  {cat.category}
                </span>
              )}

              <ul className="space-y-0.5">
                {filteredItems.map((item) => {
                  const Icon = IconMap[item.iconName] || LayoutDashboard;
                  const isActive = pathname === item.href;
                  const badge = getBadgeInfo(item);

                  return (
                    <li key={item.title}>
                      <a
                        href={item.href}
                        className={clsx(
                          'flex items-center gap-3 px-2 py-2 rounded-xl text-xs font-semibold transition-all group relative',
                          isActive
                            ? 'bg-border/30 text-text-primary border border-border/50 font-bold'
                            : 'text-text-secondary hover:bg-border/15 hover:text-text-primary border border-transparent'
                        )}
                      >
                        <Icon
                          size={14}
                          className={clsx(
                            'flex-shrink-0 transition-transform duration-100 group-hover:scale-105',
                            isActive ? 'text-accent' : 'text-muted group-hover:text-text-secondary'
                          )}
                        />

                        {isSidebarExpanded && (
                          <span className="font-sans flex-1 text-ellipsis overflow-hidden whitespace-nowrap uppercase tracking-wider text-[11px]">
                            {item.title}
                          </span>
                        )}

                        {isSidebarExpanded && badge && (
                          <Badge
                            variant={
                              badge.variant === 'danger'
                                ? 'danger'
                                : badge.variant === 'success'
                                ? 'success'
                                : badge.variant === 'warning'
                                ? 'warning'
                                : badge.variant === 'accent'
                                ? 'accent'
                                : 'secondary'
                            }
                            className="text-[8px] py-0 px-1 border-none shadow-none font-bold"
                          >
                            {badge.text}
                          </Badge>
                        )}

                        {/* Collapsed Badge Indicator */}
                        {!isSidebarExpanded && badge && (
                          <span className={clsx(
                            'absolute top-1 right-1 h-1.5 w-1.5 rounded-full border border-card',
                            badge.variant === 'danger' ? 'bg-danger' : badge.variant === 'success' ? 'bg-success' : 'bg-accent'
                          )} />
                        )}

                        {/* Tooltip on collapsed hover */}
                        {!isSidebarExpanded && (
                          <span className="absolute left-16 bg-card border border-border px-2 py-1 text-[10px] uppercase font-mono tracking-wider font-semibold rounded text-text-primary opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 shadow-xl whitespace-nowrap z-50">
                            {item.title}
                          </span>
                        )}
                      </a>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* User Session Control Footer */}
      <div className="p-3 border-t border-border/30 bg-background/25 flex flex-col gap-2">
        {isSidebarExpanded ? (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="h-7 w-7 rounded bg-border/40 flex items-center justify-center font-bold text-xs text-text-secondary font-mono border border-border">
                {user ? user.name.split(' ').map((p) => p[0]).join('').toUpperCase() : 'OP'}
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-[11px] font-semibold text-text-primary text-ellipsis overflow-hidden whitespace-nowrap leading-tight">
                  {user ? user.name : 'Plant Supervisor'}
                </span>
                <span className="text-[9px] font-mono text-muted text-ellipsis overflow-hidden whitespace-nowrap">
                  {user ? user.role.replace('_', ' ') : 'SAFETY TEAM'}
                </span>
              </div>
            </div>
            <button
              onClick={() => logout()}
              className="text-muted hover:text-danger p-1 rounded hover:bg-danger/10 transition-all focus:outline-none"
              title="Logout Operator Session"
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => logout()}
            className="text-muted hover:text-danger p-2 rounded hover:bg-danger/10 transition-all focus:outline-none mx-auto"
            title="Logout Session"
          >
            <Power size={13} />
          </button>
        )}
      </div>
    </aside>
  );
}
