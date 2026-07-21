'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { Clock } from 'lucide-react';

export default function SessionExpiredPage() {
  const router = useRouter();

  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center p-4 relative overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(239,68,68,0.03),transparent_70%)] pointer-events-none" />

      <Card className="w-full max-w-sm border-danger/30 bg-card/65 shadow-2xl relative z-10 backdrop-blur-md">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto h-8 w-8 rounded bg-danger/10 border border-danger/45 flex items-center justify-center text-danger mb-3 animate-pulse">
            <Clock size={16} />
          </div>
          <CardTitle className="text-sm tracking-wider text-danger uppercase">Session Token Expired</CardTitle>
          <CardDescription className="text-[10px] uppercase tracking-wider font-mono text-muted mt-1">
            TIMEOUT SECURE ACCESS DURATION
          </CardDescription>
        </CardHeader>

        <CardContent className="text-center space-y-4">
          <p className="text-xs text-text-secondary leading-relaxed font-sans">
            To ensure industrial safety integrity, active terminal sessions are restricted to defined shift durations. Your verification token has timed out.
          </p>

          <Button
            onClick={() => router.push('/login')}
            variant="primary"
            className="w-full uppercase text-xs tracking-widest font-mono font-bold py-2.5"
          >
            Re-Authenticate Shift
          </Button>
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <span className="text-[9px] font-mono text-muted uppercase tracking-wider">
            AUDITED DISCONNECT • ABHEDYA SECURITY
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}
