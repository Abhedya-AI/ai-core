'use client';

import * as React from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../store/useAuthStore';
import { webSocketService } from '../services/websocket/connection';
import { CommandPalette } from '../components/ui/command-palette';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

// 1. Query Client Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// 2. Custom Toast Context & Provider
export interface Toast {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'critical';
}

interface ToastContextType {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};

// 3. Command Palette Context & Provider
interface CommandPaletteContextType {
  openCommandPalette: () => void;
}

const CommandPaletteContext = React.createContext<CommandPaletteContextType | undefined>(undefined);

export const useCommandPalette = () => {
  const context = React.useContext(CommandPaletteContext);
  if (!context) throw new Error('useCommandPalette must be used within CommandPaletteProvider');
  return context;
};

// Main Providers Wrapper Component
export function Providers({ children }: { children: React.ReactNode }) {
  // Toasts State
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  const showToast = React.useCallback(({ title, message, type }: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);

    // Trigger simple alert audio beep in case of critical warnings
    if (type === 'critical' || type === 'error') {
      try {
        const audioCtx = new (window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(type === 'critical' ? 880 : 440, audioCtx.currentTime); // A5 or A4
        gainNode.gain.setValueAtTime(0.08, audioCtx.currentTime);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.15);
      } catch {
        // AudioContext browser blocks before user interaction
      }
    }

    // Dismiss toast automatically after 5 seconds (10 seconds for critical alarms)
    const timeout = type === 'critical' ? 10000 : 5000;
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, timeout);
  }, []);

  const dismissToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Command Palette State
  const [isCmdOpen, setIsCmdOpen] = React.useState(false);
  const openCommandPalette = React.useCallback(() => setIsCmdOpen(true), []);

  // Listen for Ctrl+K global keyboard shortcut
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCmdOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Auth watch session redirects
  const { isAuthenticated } = useAuthStore();
  React.useEffect(() => {
    // Session redirects can be handled here if auth drops
  }, [isAuthenticated]);

  // WebSocket Live Connection Life Cycle
  React.useEffect(() => {
    webSocketService.connect();
    return () => {
      webSocketService.disconnect();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider attribute="class" defaultTheme="dark" forcedTheme="dark" enableSystem={false}>
        <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
          <CommandPaletteContext.Provider value={{ openCommandPalette }}>
            {children}

            {/* Global Command Palette dialog */}
            <CommandPalette isOpen={isCmdOpen} onClose={() => setIsCmdOpen(false)} />

            {/* Custom toast notifications tray */}
            <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
              <AnimatePresence>
                {toasts.map((toast) => {
                  const getColors = () => {
                    switch (toast.type) {
                      case 'success':
                        return 'border-success bg-card text-success';
                      case 'warning':
                        return 'border-warning bg-card text-warning';
                      case 'error':
                        return 'border-danger bg-card text-danger';
                      case 'critical':
                        return 'border-critical bg-critical/15 text-critical glow-critical animate-pulse';
                      default:
                        return 'border-border bg-card text-accent';
                    }
                  };

                  return (
                    <motion.div
                      key={toast.id}
                      initial={{ opacity: 0, y: 20, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -20, scale: 0.95 }}
                      transition={{ duration: 0.2 }}
                      className={`pointer-events-auto flex items-start gap-3 p-3.5 border rounded-xl shadow-xl select-none ${getColors()}`}
                    >
                      <div className="mt-0.5 flex-shrink-0">
                        {toast.type === 'success' ? (
                          <CheckCircle size={16} />
                        ) : toast.type === 'error' || toast.type === 'critical' ? (
                          <AlertCircle size={16} className="text-danger" />
                        ) : (
                          <Info size={16} />
                        )}
                      </div>
                      <div className="flex-1 space-y-0.5">
                        <h4 className="text-xs font-bold uppercase tracking-wider font-mono text-text-primary">
                          {toast.title}
                        </h4>
                        <p className="text-[11px] text-text-secondary leading-relaxed font-sans">
                          {toast.message}
                        </p>
                      </div>
                      <button
                        onClick={() => dismissToast(toast.id)}
                        className="text-text-secondary hover:text-text-primary p-0.5 rounded-sm hover:bg-border/25 transition-colors"
                      >
                        <X size={12} />
                      </button>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </CommandPaletteContext.Provider>
        </ToastContext.Provider>
      </NextThemesProvider>
    </QueryClientProvider>
  );
}
