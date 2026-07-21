'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { Mail, ArrowLeft, CheckCircle, ShieldAlert } from 'lucide-react';
import { authApi } from '../../../services/api/auth';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSent, setIsSent] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError('Please input a valid registered operator email.');
      return;
    }

    setIsLoading(true);
    try {
      await authApi.forgotPassword(email);
      setIsSent(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Verification dispatch failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center p-4 relative overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.06),transparent_70%)] pointer-events-none" />

      <Card className="w-full max-w-sm border-border bg-card/65 shadow-2xl relative z-10 backdrop-blur-md">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto h-8 w-8 rounded bg-primary/10 border border-primary/45 flex items-center justify-center text-primary mb-3">
            <Mail size={16} />
          </div>
          <CardTitle className="text-sm tracking-wider text-text-primary">KEY RECOVERY PANEL</CardTitle>
          <CardDescription className="text-[10px] uppercase tracking-wider font-mono text-muted mt-1">
            REQUEST KEY RESTORATION TOKEN
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isSent ? (
            <div className="space-y-4 text-center">
              <div className="p-3 border border-success/30 bg-success/5 rounded-xl flex items-start gap-2.5 text-xs text-success font-mono text-left">
                <CheckCircle size={14} className="flex-shrink-0 mt-0.5" />
                <span>An authorized token reset link has been dispatched to your email registry. Verify your inbox logs to continue.</span>
              </div>
              <Button variant="secondary" className="w-full text-xs font-mono uppercase tracking-wider" onClick={() => router.push('/login')}>
                Back to Terminal
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 border border-danger/30 bg-danger/5 rounded-xl flex items-start gap-2.5 text-xs text-danger font-mono">
                  <ShieldAlert size={14} className="flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-wider block">
                  Registry Email
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-3 flex items-center text-muted">
                    <Mail size={13} />
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@abhedya.ai"
                    className="w-full bg-background/50 border border-border focus:border-border/80 focus:ring-1 focus:ring-accent rounded-xl pl-9 pr-3 py-2 text-xs text-text-primary placeholder-muted/65 focus:outline-none"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full uppercase text-xs tracking-widest font-mono font-bold py-2.5 mt-2"
                isLoading={isLoading}
              >
                Send Reset Link
              </Button>
            </form>
          )}
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <button
            onClick={() => router.push('/login')}
            className="text-[9px] font-mono text-muted hover:text-text-primary flex items-center gap-1.5 uppercase tracking-wider transition-colors"
          >
            <ArrowLeft size={10} />
            <span>Back to Login</span>
          </button>
        </CardFooter>
      </Card>
    </div>
  );
}
