'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../../store/useAuthStore';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { Lock, Mail, Eye, EyeOff, ShieldAlert } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError, isTwoFactorRequired } = useAuthStore();
  const [email, setEmail] = React.useState('d.vance@abhedya.ai');
  const [password, setPassword] = React.useState('password123');
  const [showPassword, setShowPassword] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  React.useEffect(() => {
    clearError();
  }, [clearError]);

  React.useEffect(() => {
    if (isTwoFactorRequired) {
      router.push('/two-factor');
    }
  }, [isTwoFactorRequired, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!email || !password) {
      setFormError('All authentication fields are required.');
      return;
    }

    const success = await login(email, password);
    if (success) {
      router.push('/two-factor');
    }
  };

  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Visual background details */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.06),transparent_70%)] pointer-events-none" />
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-border/50 to-transparent" />

      <Card className="w-full max-w-sm border-border bg-card/65 shadow-2xl relative z-10 backdrop-blur-md">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto h-8 w-8 rounded bg-primary flex items-center justify-center font-bold text-sm text-text-primary glow-primary font-mono border border-primary/50 mb-3">
            Ω
          </div>
          <CardTitle className="text-base tracking-widest text-text-primary">ABHEDYA AI</CardTitle>
          <CardDescription className="text-[11px] uppercase tracking-wider font-mono text-muted">
            OPERATIONAL SECURITY TERMINAL
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display errors */}
            {(formError || error) && (
              <div className="p-3 border border-danger/30 bg-danger/5 rounded-xl flex items-start gap-2.5 text-xs text-danger font-mono">
                <ShieldAlert size={14} className="flex-shrink-0 mt-0.5" />
                <span>{formError || error}</span>
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1">
              <label className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-wider block">
                Operator Email
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
                  autoComplete="username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-wider block">
                  Access Key
                </label>
                <a
                  href="/forgot-password"
                  className="text-[9px] font-mono text-accent hover:text-text-primary uppercase tracking-wider"
                >
                  Forgot Key?
                </a>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-3 flex items-center text-muted">
                  <Lock size={13} />
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter access key"
                  className="w-full bg-background/50 border border-border focus:border-border/80 focus:ring-1 focus:ring-accent rounded-xl pl-9 pr-10 py-2 text-xs text-text-primary placeholder-muted/65 focus:outline-none"
                  disabled={isLoading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-3 flex items-center text-muted hover:text-text-primary"
                >
                  {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              className="w-full uppercase text-xs tracking-widest font-mono font-bold py-2.5 mt-2"
              isLoading={isLoading}
            >
              Sign In
            </Button>
          </form>
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <span className="text-[9px] font-mono text-muted uppercase tracking-wider">
            SECURED ENDPOINT • SYSTEM AUDITED
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}
