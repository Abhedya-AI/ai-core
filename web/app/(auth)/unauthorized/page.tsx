'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { ShieldX } from 'lucide-react';

export default function UnauthorizedPage() {
  const router = useRouter();

  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center p-4 relative overflow-hidden select-none">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(185,28,28,0.06),transparent_70%)] pointer-events-none" />

      <Card className="w-full max-w-sm border-critical bg-card/65 shadow-2xl relative z-10 backdrop-blur-md">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto h-8 w-8 rounded bg-critical/20 border border-critical flex items-center justify-center text-critical mb-3 animate-pulse">
            <ShieldX size={16} />
          </div>
          <CardTitle className="text-sm tracking-wider text-critical uppercase font-bold">Access Unauthorized</CardTitle>
          <CardDescription className="text-[10px] uppercase tracking-wider font-mono text-muted mt-1">
            VERIFICATION LEVEL INSUFFICIENT
          </CardDescription>
        </CardHeader>

        <CardContent className="text-center space-y-4">
          <p className="text-xs text-text-secondary leading-relaxed font-sans">
            Your current operator role does not possess the credentials to execute command overrides on this module. Incident has been logged to the plant safety log.
          </p>

          <div className="flex gap-2">
            <Button
              onClick={() => router.push('/')}
              variant="secondary"
              className="w-1/2 uppercase text-[10px] tracking-wider font-mono font-bold py-2"
            >
              Control Center
            </Button>
            <Button
              onClick={() => router.push('/login')}
              variant="accent"
              className="w-1/2 uppercase text-[10px] tracking-wider font-mono font-bold py-2"
            >
              Switch Role
            </Button>
          </div>
        </CardContent>

        <CardFooter className="justify-center border-t border-border/30 bg-background/15 py-3">
          <span className="text-[9px] font-mono text-critical uppercase tracking-wider font-bold">
            SECURITY EXCEPTION REPORTED • ID: LOG-4820
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}
