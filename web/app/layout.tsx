import type { Metadata, Viewport } from 'next';
import { Providers } from './providers';
import './globals.css';

export const metadata: Metadata = {
  title: 'ABHEDYA AI | Industrial Operating System',
  description: 'Enterprise safety intelligence, real-time telemetry grid orchestration, and multi-agent industrial hazard mitigation.',
  icons: {
    icon: '/favicon.ico',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full dark" style={{ colorScheme: 'dark' }} suppressHydrationWarning>
      <body className="min-h-full bg-background text-text-primary antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
