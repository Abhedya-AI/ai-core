'use client';

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent, KpiCard, MetricCard } from '../../components/ui/card';
import { Badge, StatusIndicator } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { DataTable, Column } from '../../components/ui/data-table';
import { useSensorsStore } from '../../store/useSensorsStore';
import { useAlertsStore } from '../../store/useAlertsStore';
import { useAuthStore } from '../../store/useAuthStore';
import { useToast } from '../providers';
import { Alert } from '../../types';
import { ShieldCheck, Cpu, Bell, KeyRound, Wrench, RefreshCw, Command, Play } from 'lucide-react';

export default function MissionControlPage() {
  const { sensors } = useSensorsStore();
  const { alerts, acknowledgeAlert } = useAlertsStore();
  const { user } = useAuthStore();
  const { showToast } = useToast();

  const handleSimulateAlert = () => {
    showToast({
      title: 'Manual Diagnostics Triggered',
      message: 'Self-test diagnostic routine initiated across sensor sectors.',
      type: 'info',
    });
  };

  // Active alarms subset
  const activeAlerts = React.useMemo(() => {
    return alerts.filter((a) => a.status !== 'RESOLVED').slice(0, 5);
  }, [alerts]);

  // Alert Columns config
  const alertColumns: Column<Alert>[] = [
    {
      header: 'ID',
      accessor: 'id',
      className: 'w-16 font-mono text-muted',
    },
    {
      header: 'Timestamp',
      accessor: (row) => new Date(row.timestamp).toLocaleTimeString(),
      className: 'w-24 text-muted',
    },
    {
      header: 'Severity',
      accessor: (row) => (
        <Badge
          variant={
            row.severity === 'CRITICAL'
              ? 'critical'
              : row.severity === 'DANGER'
              ? 'danger'
              : row.severity === 'WARNING'
              ? 'warning'
              : 'primary'
          }
          className="text-[9px] py-0 px-1 font-bold"
        >
          {row.severity}
        </Badge>
      ),
      className: 'w-24',
    },
    {
      header: 'Location',
      accessor: 'location',
      className: 'w-48 text-text-primary uppercase tracking-wider',
    },
    {
      header: 'Incident Alert Message',
      accessor: 'message',
      className: 'text-text-secondary font-sans',
    },
    {
      header: 'Action',
      accessor: (row) => (
        row.status === 'ACTIVE' ? (
          <Button
            size="sm"
            variant="accent"
            className="text-[9px] py-0.5 px-2 font-mono uppercase tracking-wider"
            onClick={(e) => {
              e.stopPropagation();
              if (user) acknowledgeAlert(row.id, user.id);
              showToast({
                title: 'Alert Acknowledged',
                message: `Incident ${row.id} has been logged under your operator session.`,
                type: 'success',
              });
            }}
          >
            Acknowledge
          </Button>
        ) : (
          <span className="text-[10px] font-mono text-success uppercase tracking-wider font-semibold">
            ACKNOWLEDGED
          </span>
        )
      ),
      className: 'w-32 text-right',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-border/30 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary uppercase font-mono">
            Mission Control Console
          </h1>
          <p className="text-xs text-muted mt-0.5 leading-relaxed font-mono">
            ABHEDYA OPERATING SYSTEM • FOUNDATION GRID MONITOR
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="accent" onClick={handleSimulateAlert}>
            <Play size={10} />
            <span>Run Grid Self-Test</span>
          </Button>
        </div>
      </div>

      {/* Grid status cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Overall Safety Index"
          value="98.4"
          unit="%"
          status="NORMAL"
          subtitle="Toxics & pressure lines secure"
        />
        <KpiCard
          title="Active Hazards Queue"
          value={activeAlerts.length}
          unit="ALTS"
          status={activeAlerts.length > 0 ? 'WARNING' : 'NORMAL'}
          subtitle={`${alerts.filter(a => a.status === 'RESOLVED').length} alarms cleared today`}
        />
        <KpiCard
          title="Total Sensors Grid"
          value={sensors.length}
          unit="NODES"
          status="NORMAL"
          subtitle={`${sensors.filter(s => s.status === 'CRITICAL').length} nodes warning flags`}
        />
        <KpiCard
          title="Operator Session"
          value={user ? user.name.split(' ')[0] : 'Supervisor'}
          unit={user ? user.role.split('_')[1] : 'TEAM'}
          status="NORMAL"
          subtitle="Authorized secure terminal"
        />
      </div>

      {/* Main console content split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Core telemetry feeds summary */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active alerts grid */}
          <Card borderAccent="none">
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <div>
                <CardTitle className="text-xs tracking-wider">Active Incident Queue</CardTitle>
                <span className="text-[9px] font-mono text-muted uppercase">REAL-TIME HAZARD THREADS</span>
              </div>
              <StatusIndicator status={activeAlerts.length > 0 ? 'WARNING' : 'STABLE'} />
            </CardHeader>
            <CardContent className="p-0">
              <DataTable
                columns={alertColumns}
                data={activeAlerts}
                keyExtractor={(row) => row.id}
                emptyMessage="All plant sectors operating within safe parameters."
              />
            </CardContent>
          </Card>

          {/* Plant Telemetry status nodes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sensors.slice(0, 4).map((sensor) => (
              <MetricCard
                key={sensor.id}
                label={sensor.name}
                value={sensor.value}
                min={sensor.minThreshold}
                max={sensor.maxThreshold}
                unit={sensor.unit}
                status={sensor.status === 'CRITICAL' ? 'CRITICAL' : sensor.status === 'WARNING' ? 'WARNING' : 'NORMAL'}
              />
            ))}
          </div>
        </div>

        {/* Right side operational checklist / readiness verification */}
        <div className="space-y-6">
          <Card className="border-border bg-card/40">
            <CardHeader className="py-3">
              <CardTitle className="text-xs tracking-wider">Foundation Checklist</CardTitle>
              <span className="text-[9px] font-mono text-muted uppercase">VERIFYING OPERATING SYSTEM SETUP</span>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3 font-mono text-xs text-text-secondary">
                
                <div className="flex items-center justify-between border-b border-border/10 pb-2">
                  <div className="flex items-center gap-2">
                    <ShieldCheck size={12} className="text-success" />
                    <span>Next.js App Router Setup</span>
                  </div>
                  <Badge variant="success" className="text-[8px]">ACTIVE</Badge>
                </div>

                <div className="flex items-center justify-between border-b border-border/10 pb-2">
                  <div className="flex items-center gap-2">
                    <Cpu size={12} className="text-success" />
                    <span>Zustand State Stores (12)</span>
                  </div>
                  <Badge variant="success" className="text-[8px]">MOUNTED</Badge>
                </div>

                <div className="flex items-center justify-between border-b border-border/10 pb-2">
                  <div className="flex items-center gap-2">
                    <Bell size={12} className="text-success" />
                    <span>Toast Alert Provider</span>
                  </div>
                  <Badge variant="success" className="text-[8px]">ONLINE</Badge>
                </div>

                <div className="flex items-center justify-between border-b border-border/10 pb-2">
                  <div className="flex items-center gap-2">
                    <KeyRound size={12} className="text-success" />
                    <span>Session Auth Guard Routing</span>
                  </div>
                  <Badge variant="success" className="text-[8px]">VERIFIED</Badge>
                </div>

                <div className="flex items-center justify-between border-b border-border/10 pb-2">
                  <div className="flex items-center gap-2">
                    <Wrench size={12} className="text-success" />
                    <span>Premium Reusable Components</span>
                  </div>
                  <Badge variant="success" className="text-[8px]">30+ LIBS</Badge>
                </div>

                <div className="flex items-center justify-between pb-1">
                  <div className="flex items-center gap-2">
                    <RefreshCw size={12} className="text-accent animate-spin" />
                    <span>WebSocket Telemetry Mock</span>
                  </div>
                  <Badge variant="accent" className="text-[8px]">STREAMING</Badge>
                </div>

              </div>
            </CardContent>
          </Card>

          {/* Quick Shortcuts Hint */}
          <Card className="border-border bg-card/25 border-dashed">
            <CardContent className="py-4 text-center space-y-2">
              <Command size={18} className="mx-auto text-muted" />
              <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wide">
                Keyboard System Command Palette
              </h4>
              <p className="text-[10px] text-muted max-w-xs mx-auto leading-relaxed">
                Press <kbd className="bg-border/40 px-1 py-0.5 border border-border rounded text-text-primary font-bold">Ctrl + K</kbd> anywhere inside the application viewport to launch command options.
              </p>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
