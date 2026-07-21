'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../../store/useAuthStore';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { ShieldAlert, KeyRound } from 'lucide-react';

export default function TwoFactorPage() {
  const router = useRouter();
  const { verifyTwoFactor, isLoading, error, clearError } = useAuthStore();
  const [code, setCode] = React.useState('');
  const [formError, setFormError] = React.useState<string | null>(null);

  React.useEffect(() => {
    clearError();
  }, [clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (code.length !== 6 || !/^\d+$/.test(code)) {
      setFormError('Please enter a valid 6-digit verification code.');
      return;
    }

    const success = await verifyTwoFactor(code);
    if (success) {
      router.push('/');
    }
  };

  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center p-4 relative overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.06),transparent_70%)] pointer-events-none" />

      <Card className="w-full max-w-sm border-border bg-card/65 shadow-2xl relative z-10 backdrop-blur-md">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto h-8 w-8 rounded bg-primary/10 border border-primary/45 flex items-center justify-center text-primary mb-3">
            <KeyRound size={16} />
          </div>
          <CardTitle className="text-sm tracking-wider text-text-primary">TWO-FACTOR AUTHENTICATION</CardTitle>
          <CardDescription className="text-[10px] uppercase tracking-wider font-mono text-muted mt-1">
            MOCK CODE IS &quot;123456&quot; OR &quot;000000&quot;
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

            {/* Input code block */}
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-wider block text-center">
                Enter 6-Digit Secure Token
              </label>
              <input
                type="text"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000 000"
                className="w-full bg-background/50 border border-border focus:border-border/80 focus:ring-1 focus:ring-accent rounded-xl py-3 text-lg font-mono text-center tracking-[0.5em] text-text-primary focus:outline-none placeholder-muted/30"
                disabled={isLoading}
                autoFocus
              />
            </div>

            {/* Verification Button */}
            <Button
              type="submit"
              variant="primary"
              className="w-full uppercase text-xs tracking-widest font-mono font-bold py-2.5 mt-2"
              isLoading={isLoading}
            >
              Verify Code
            </Button>
          </form>
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <button
            onClick={() => router.push('/login')}
            className="text-[9px] font-mono text-muted hover:text-text-primary uppercase tracking-wider transition-colors"
          >
            Cancel Authentication
          </button>
        </CardFooter>
      </Card>
    </div>
  );
}
