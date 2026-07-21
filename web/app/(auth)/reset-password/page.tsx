'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { Lock, CheckCircle, ShieldAlert } from 'lucide-react';
import { authApi } from '../../../services/api/auth';

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSuccess, setIsSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!password || !confirmPassword) {
      setError('Both key parameters are required.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Access keys do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await authApi.resetPassword('mock-reset-token', password);
      setIsSuccess(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Key recalibration failed.');
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
            <Lock size={16} />
          </div>
          <CardTitle className="text-sm tracking-wider text-text-primary">ACCESS KEY CALIBRATION</CardTitle>
          <CardDescription className="text-[10px] uppercase tracking-wider font-mono text-muted mt-1">
            ESTABLISH NEW ACCESS CREDENTIALS
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isSuccess ? (
            <div className="space-y-4 text-center">
              <div className="p-3 border border-success/30 bg-success/5 rounded-xl flex items-start gap-2.5 text-xs text-success font-mono text-left">
                <CheckCircle size={14} className="flex-shrink-0 mt-0.5" />
                <span>Access key updated successfully. Secure terminal is now calibrated.</span>
              </div>
              <Button variant="primary" className="w-full text-xs font-mono uppercase tracking-wider" onClick={() => router.push('/login')}>
                Go to login
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
                  New Access Key
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full bg-background/50 border border-border focus:border-border/80 focus:ring-1 focus:ring-accent rounded-xl px-3 py-2 text-xs text-text-primary focus:outline-none"
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-wider block">
                  Confirm Access Key
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-type access key"
                  className="w-full bg-background/50 border border-border focus:border-border/80 focus:ring-1 focus:ring-accent rounded-xl px-3 py-2 text-xs text-text-primary focus:outline-none"
                  disabled={isLoading}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full uppercase text-xs tracking-widest font-mono font-bold py-2.5 mt-2"
                isLoading={isLoading}
              >
                Reset Access Key
              </Button>
            </form>
          )}
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <button
            onClick={() => router.push('/login')}
            className="text-[9px] font-mono text-muted hover:text-text-primary uppercase tracking-wider transition-colors"
          >
            Back to login
          </button>
        </CardFooter>
      </Card>
    </div>
  );
}
