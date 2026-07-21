import * as React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Search, Terminal, ArrowRight } from 'lucide-react';
import { ROUTES } from '../../constants/routes';

interface CommandOption {
  title: string;
  category: string;
  action: () => void;
  shortcut?: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette = ({ isOpen, onClose }: CommandPaletteProps) => {
  const [query, setQuery] = React.useState('');
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const commands: CommandOption[] = React.useMemo(() => {
    const pushRoute = (path: string) => {
      if (typeof window !== 'undefined') {
        window.location.href = path;
      }
      onClose();
    };

    return [
      { title: 'Navigate to Mission Control', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.home), shortcut: 'G H' },
      { title: 'Navigate to Sensor Grid', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.sensors), shortcut: 'G S' },
      { title: 'Navigate to Live Alerts Queue', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.alerts), shortcut: 'G A' },
      { title: 'Navigate to Work Permits Desk', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.permits), shortcut: 'G P' },
      { title: 'Navigate to Digital Twin 3D View', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.digitalTwin), shortcut: 'G T' },
      { title: 'Navigate to Knowledge Graph Explorer', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.knowledgeGraph), shortcut: 'G K' },
      { title: 'Navigate to Compliance Center', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.compliance), shortcut: 'G C' },
      { title: 'Navigate to Settings Panel', category: 'Navigation', action: () => pushRoute(ROUTES.dashboard.settings), shortcut: 'G O' },
      { title: 'Toggle High Contrast Theme Mode', category: 'Preferences', action: () => {
        // Mock preferences toggle
        onClose();
      } },
      { title: 'Calibrate Plant Sensor Grid', category: 'System Action', action: () => {
        console.log('[CMD PALETTE] Triggering sensor calibration...');
        onClose();
      }, shortcut: 'CMD C' },
      { title: 'Initialize Emergency Shutdown Checklist', category: 'Emergency Actions', action: () => {
        pushRoute(ROUTES.dashboard.emergency);
      }, shortcut: 'ALT F4' },
    ];
  }, [onClose]);

  const filtered = React.useMemo(() => {
    if (!query) return commands;
    const cleanQuery = query.toLowerCase();
    return commands.filter(
      (c) =>
        c.title.toLowerCase().includes(cleanQuery) ||
        c.category.toLowerCase().includes(cleanQuery)
    );
  }, [query, commands]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filtered.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].action();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Dialog Container */}
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="relative w-full max-w-lg bg-card border border-border shadow-2xl rounded-xl overflow-hidden flex flex-col max-h-[50vh]"
          >
            {/* Input Header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-border/30">
              <Search size={16} className="text-muted" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search commands, views, or telemetry actions..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                className="flex-1 bg-transparent border-none text-text-primary text-sm font-sans placeholder-muted focus:outline-none focus:ring-0"
              />
              <span className="px-1.5 py-0.5 border border-border/80 rounded bg-border/20 text-[9px] font-mono text-muted uppercase">
                ESC
              </span>
            </div>

            {/* List Results */}
            <div className="flex-1 overflow-y-auto p-2 min-h-0 divide-y divide-border/10">
              {filtered.length === 0 ? (
                <div className="p-4 text-center text-xs font-mono text-muted uppercase">
                  No matching system directives found.
                </div>
              ) : (
                filtered.map((cmd, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <div
                      key={cmd.title}
                      onClick={() => cmd.action()}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer select-none transition-colors ${
                        isSelected
                          ? 'bg-border/30 text-text-primary border border-border/60'
                          : 'text-text-secondary hover:bg-border/10 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Terminal size={14} className={isSelected ? 'text-accent' : 'text-muted'} />
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold font-sans">{cmd.title}</span>
                          <span className="text-[9px] font-mono text-muted uppercase tracking-wider">
                            {cmd.category}
                          </span>
                        </div>
                      </div>
                      {cmd.shortcut ? (
                        <span className="text-[9px] font-mono text-muted px-1.5 py-0.5 border border-border/40 rounded bg-background/35">
                          {cmd.shortcut}
                        </span>
                      ) : (
                        isSelected && <ArrowRight size={12} className="text-accent animate-pulse" />
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
