'use client';

import * as React from 'react';
import { Sidebar } from '../../components/layout/sidebar';
import { TopNav } from '../../components/layout/top-nav';
import { useCopilotStore } from '../../store/useCopilotStore';
import { useAuthStore } from '../../store/useAuthStore';
import { redirect } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { Send, Sparkles, X, Terminal, Cpu, ShieldAlert } from 'lucide-react';
import { CopilotMessage } from '../../types';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const { isOpen: isCopilotOpen, setOpen: setCopilotOpen, messages, addMessage, isThinking, setThinking } = useCopilotStore();
  const [prompt, setPrompt] = React.useState('');
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  // Authentication Guard redirecting to login if user not authenticated
  React.useEffect(() => {
    if (!isAuthenticated) {
      redirect('/login');
    }
  }, [isAuthenticated]);

  // Autoscroll chat log
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSendPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isThinking) return;

    const userPrompt = prompt.trim();
    setPrompt('');
    
    // 1. Add User Prompt
    addMessage({
      sender: 'USER',
      content: userPrompt,
    });

    // 2. Set Thinking Loader
    setThinking(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 3. Add AI Simulated Response
    let responseContent = `Analyzing telemetry and asset dependencies for query: "${userPrompt}". All units report within normal limits.`;
    let references: NonNullable<CopilotMessage['references']> = [];

    if (userPrompt.toLowerCase().includes('leak') || userPrompt.toLowerCase().includes('gas') || userPrompt.toLowerCase().includes('h2s')) {
      responseContent = 'CRITICAL ALERT: Sensor **Gas Detector H2S Point 04** in Sector C reports active levels of 12.8 ppm. Sector C has been flagged with restricted access permit WP-2026-9042.';
      references = [
        { type: 'SENSOR', id: 'sns-gas-03', name: 'Gas Detector H2S' },
        { type: 'ALERT', id: 'alt-1029', name: 'Critical Gas Release' },
      ];
    } else if (userPrompt.toLowerCase().includes('permit') || userPrompt.toLowerCase().includes('hot work')) {
      responseContent = 'Currently, there are **12 Active Permits** in the plant. The most recent permit approved is **WP-2026-9042** (Reactor catalyst replacing, assigned to Marcus Brody).';
      references = [
        { type: 'PERMIT', id: 'pmt-3011', name: 'WP-2026-9042' },
      ];
    }

    addMessage({
      sender: 'AI',
      content: responseContent,
      references,
    });
    setThinking(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen bg-background flex items-center justify-center font-mono text-xs uppercase text-muted">
        Authorizing shift access...
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-background text-text-primary overflow-hidden font-sans">
      {/* Sidebar navigation drawer */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <TopNav />

        {/* Dashboard page viewport */}
        <main className="flex-1 overflow-y-auto p-6 min-h-0 bg-background">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="h-full w-full"
          >
            {children}
          </motion.div>
        </main>

        {/* Copilot sliding drawer */}
        <AnimatePresence>
          {isCopilotOpen && (
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'tween', ease: 'easeInOut', duration: 0.22 }}
              className="absolute right-0 top-0 bottom-0 z-50 w-96 bg-card border-l border-border shadow-2xl flex flex-col h-full overflow-hidden select-none"
            >
              {/* Header */}
              <div className="h-14 border-b border-border/30 px-4 flex items-center justify-between bg-background/25">
                <div className="flex items-center gap-2 text-accent">
                  <Sparkles size={14} className="animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-widest font-mono">
                    ABHEDYA SAFETY COPILOT
                  </span>
                </div>
                <button
                  onClick={() => setCopilotOpen(false)}
                  className="text-muted hover:text-text-primary p-1 rounded-sm hover:bg-border/20 transition-all focus:outline-none"
                >
                  <X size={15} />
                </button>
              </div>

              {/* Chat Message Logs */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
                {messages.map((msg) => {
                  const isAi = msg.sender === 'AI';
                  return (
                    <div
                      key={msg.id}
                      className={`flex flex-col space-y-1.5 max-w-[85%] ${
                        isAi ? 'mr-auto' : 'ml-auto items-end'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 text-[9px] font-mono text-muted uppercase">
                        <span>{isAi ? 'SAFETY AGENT' : 'OPERATOR'}</span>
                        <span>•</span>
                        <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div
                        className={`text-xs p-3 rounded-xl border leading-relaxed font-sans ${
                          isAi
                            ? 'bg-background/40 border-border text-text-primary'
                            : 'bg-primary/10 border-primary text-text-primary'
                        }`}
                      >
                        <p>{msg.content}</p>

                        {/* Message References chips */}
                        {msg.references && msg.references.length > 0 && (
                          <div className="mt-3 pt-2 border-t border-border/20 flex flex-wrap gap-1.5">
                            {msg.references.map((ref) => (
                              <span
                                key={ref.id}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 border border-border bg-card/60 text-[9px] font-mono font-semibold rounded text-accent uppercase hover:border-accent/40 cursor-pointer"
                              >
                                {ref.type === 'SENSOR' ? (
                                  <Cpu size={8} />
                                ) : ref.type === 'ALERT' ? (
                                  <ShieldAlert size={8} className="text-danger" />
                                ) : (
                                  <Terminal size={8} />
                                )}
                                <span>{ref.name}</span>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Thinking Loading Indicator */}
                {isThinking && (
                  <div className="flex flex-col space-y-1.5 max-w-[85%] mr-auto">
                    <div className="text-[9px] font-mono text-muted uppercase">
                      SAFETY AGENT IS COMPILING...
                    </div>
                    <div className="bg-background/40 border border-border p-3 rounded-xl flex items-center gap-2">
                      <div className="flex space-x-1">
                        <span className="h-1.5 w-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="h-1.5 w-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="h-1.5 w-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input Prompt Box */}
              <form
                onSubmit={handleSendPrompt}
                className="p-3 border-t border-border/30 bg-background/20 flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Query plant status or isolation valves..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={isThinking}
                  className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-xs font-sans text-text-primary focus:outline-none focus:border-border/80 focus:ring-1 focus:ring-accent disabled:opacity-50 placeholder-muted"
                />
                <button
                  type="submit"
                  disabled={!prompt.trim() || isThinking}
                  className="h-8 w-8 rounded-xl bg-primary text-text-primary hover:bg-blue-700 flex items-center justify-center transition-all disabled:opacity-40 disabled:hover:bg-primary focus:outline-none"
                >
                  <Send size={12} />
                </button>
              </form>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
