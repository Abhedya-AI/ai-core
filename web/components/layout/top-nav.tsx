'use client';

import * as React from 'react';
import { useCommandPalette } from '../../app/providers';
import { useNotificationsStore } from '../../store/useNotificationsStore';
import { useCopilotStore } from '../../store/useCopilotStore';
import { Search, Bell, Sparkles, AlertTriangle, ShieldCheck, Check } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

export function TopNav() {
  const { openCommandPalette } = useCommandPalette();
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotificationsStore();
  const { setOpen: setCopilotOpen, isOpen: isCopilotOpen } = useCopilotStore();

  // Time Sync Ticker
  const [timeStr, setTimeStr] = React.useState('');
  React.useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(
        d.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }) + ' GMT'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Notifications Tray State
  const [isTrayOpen, setIsTrayOpen] = React.useState(false);
  const trayRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (trayRef.current && !trayRef.current.contains(e.target as Node)) {
        setIsTrayOpen(false);
      }
    };
    if (isTrayOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [isTrayOpen]);

  return (
    <header className="h-14 border-b border-border/30 bg-card/85 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between px-6 select-none">
      {/* Search Input Bar (Triggers Ctrl+K) */}
      <div className="flex items-center gap-4 w-96">
        <button
          onClick={openCommandPalette}
          className="flex items-center justify-between w-full px-3 py-1.5 rounded-xl border border-border bg-background/25 text-left text-xs text-muted hover:border-border/75 transition-all outline-none"
        >
          <div className="flex items-center gap-2">
            <Search size={13} />
            <span>Search telemetry nodes, logs...</span>
          </div>
          <kbd className="font-mono text-[9px] px-1.5 py-0.5 border border-border/80 rounded bg-border/20 uppercase tracking-wider">
            CTRL K
          </kbd>
        </button>
      </div>

      {/* Center/Right Info Bar */}
      <div className="flex items-center gap-4">
        {/* Environment Safety Status Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-xl border border-success/30 bg-success/5 text-[10px] font-mono font-bold text-success uppercase tracking-widest">
          <ShieldCheck size={12} className="animate-pulse" />
          <span>PLANT 04 - SECURE</span>
        </div>

        {/* Live synchronized Clock */}
        <div className="text-[11px] font-mono font-semibold tracking-wider text-text-secondary border-l border-border/30 pl-4">
          {timeStr || '00:00:00 GMT'}
        </div>

        {/* Connection status Indicator */}
        <div className="flex items-center gap-1.5 border-l border-border/30 pl-4 text-[10px] font-mono text-muted uppercase">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
          </span>
          <span className="hidden md:inline text-[9px] tracking-wider text-text-secondary font-semibold">FEED STABLE</span>
        </div>

        {/* AI Copilot Toggle Button */}
        <button
          onClick={() => setCopilotOpen(!isCopilotOpen)}
          className={`h-8 px-3 rounded-xl border flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider transition-all focus:outline-none ${
            isCopilotOpen
              ? 'bg-accent/15 border-accent text-accent glow-accent font-bold'
              : 'border-border text-muted hover:text-text-primary hover:bg-border/10'
          }`}
          title="Toggle Safety AI Copilot Panel"
        >
          <Sparkles size={13} className={isCopilotOpen ? 'animate-pulse' : ''} />
          <span className="hidden lg:inline text-[10px] tracking-widest font-semibold">COPILOT</span>
        </button>

        {/* Live Notification Icon Bell */}
        <div className="relative" ref={trayRef}>
          <button
            onClick={() => setIsTrayOpen(!isTrayOpen)}
            className={`h-8 w-8 rounded-xl border flex items-center justify-center transition-all focus:outline-none ${
              isTrayOpen || unreadCount > 0
                ? 'bg-card border-border/80 text-text-primary'
                : 'border-border text-muted hover:text-text-primary hover:bg-border/10'
            }`}
          >
            <Bell size={14} className={unreadCount > 0 ? 'animate-swing' : ''} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-critical rounded-sm flex items-center justify-center text-[9px] font-bold text-text-primary font-mono glow-critical border border-critical">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notification dropdown Panel */}
          <AnimatePresence>
            {isTrayOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-80 bg-card border border-border shadow-2xl rounded-xl overflow-hidden flex flex-col max-h-96 z-50"
              >
                {/* Tray Header */}
                <div className="flex items-center justify-between p-3 border-b border-border/30 bg-background/25">
                  <span className="text-[10px] font-bold tracking-wider font-mono uppercase text-text-secondary">
                    Operational Feed ({unreadCount})
                  </span>
                  {unreadCount > 0 && (
                    <button
                      onClick={() => markAllAsRead()}
                      className="text-[9px] font-mono text-accent hover:text-text-primary font-semibold flex items-center gap-1 uppercase"
                    >
                      <Check size={10} />
                      <span>Clear All</span>
                    </button>
                  )}
                </div>

                {/* Notifications List */}
                <div className="flex-1 overflow-y-auto divide-y divide-border/10">
                  {notifications.length === 0 ? (
                    <div className="p-6 text-center text-xs font-mono text-muted uppercase">
                      No system events reported.
                    </div>
                  ) : (
                    notifications.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => markAsRead(notif.id)}
                        className={`p-3 cursor-pointer transition-colors ${
                          notif.read ? 'opacity-60 bg-transparent' : 'bg-border/10 hover:bg-border/15'
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          {notif.category === 'ALERT' && (
                            <AlertTriangle size={12} className="text-danger mt-0.5 flex-shrink-0" />
                          )}
                          <div className="flex-1 space-y-0.5">
                            <h5 className="text-[11px] font-semibold text-text-primary uppercase tracking-wide">
                              {notif.title}
                            </h5>
                            <p className="text-[10px] text-text-secondary leading-relaxed font-sans">
                              {notif.message}
                            </p>
                            <span className="text-[8px] font-mono text-muted uppercase block pt-0.5">
                              {new Date(notif.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
