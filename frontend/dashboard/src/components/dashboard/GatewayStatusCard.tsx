import React from 'react';
import { GatewayHealth, GatewayMetrics, SensorNode } from '../../types/api';
import { Server, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

interface GatewayStatusCardProps {
  health: GatewayHealth | null;
  metrics: GatewayMetrics | null;
  isGatewayOnline: boolean;
  connectedNodes: SensorNode[];
}

export const GatewayStatusCard: React.FC<GatewayStatusCardProps> = ({
  health,
  metrics,
  isGatewayOnline,
  connectedNodes,
}) => {
  const queueSize = metrics?.current_queue_size ?? health?.queue_size ?? 0;
  const isQueuePending = queueSize > 0;
  const backendConnected = health?.backend_connected ?? false;

  return (
    <div className="rounded-2xl border-2 border-ink bg-cream p-4 sm:p-6 hard-shadow sm:rounded-[2rem] font-mono space-y-4">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b-2 border-ink/20 pb-3">
        <div className="flex items-center gap-3">
          <span className="grid size-10 sm:size-12 shrink-0 place-items-center rounded-2xl bg-lime border-2 border-ink text-xl hard-shadow-xs text-ink">
            <Server className="w-5 h-5 sm:w-6 sm:h-6" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm sm:text-base font-bold text-ink uppercase tracking-wider">
                Edge Gateway · Store & Forward Tier
              </h3>
              <span className="rounded-full border border-ink bg-amber px-2 py-0.2 text-[9px] font-bold uppercase tracking-wider text-ink">
                Port 9000
              </span>
            </div>
            <p className="text-[11px] text-ink/70">
              Persistent local SQLite buffer queue · {connectedNodes.length} Node{connectedNodes.length === 1 ? '' : 's'} linked · Zero data loss
            </p>
          </div>
        </div>

        {/* Status Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <div
            className={cn(
              'flex items-center gap-1.5 rounded-full border-2 border-ink px-3 py-1 text-[11px] font-bold uppercase tracking-wider hard-shadow-xs',
              isGatewayOnline ? 'bg-mint text-ink' : 'bg-coral text-cream animate-pulse'
            )}
          >
            <span
              className={cn(
                'size-2 rounded-full',
                isGatewayOnline ? 'bg-emerald-700 animate-ping' : 'bg-cream'
              )}
            />
            <span>{isGatewayOnline ? 'Gateway Active' : 'Gateway Down'}</span>
          </div>

          <div
            className={cn(
              'flex items-center gap-1.5 rounded-full border-2 border-ink px-3 py-1 text-[11px] font-bold uppercase tracking-wider hard-shadow-xs',
              backendConnected ? 'bg-lime text-ink' : 'bg-amber-200 text-ink'
            )}
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>{backendConnected ? 'Uplink Synced' : 'Buffering Offline'}</span>
          </div>
        </div>
      </div>

      {/* 4 Neo-Brutalist Metric Tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Metric 1: Received */}
        <div className="rounded-xl sm:rounded-2xl border-2 border-ink bg-sky p-3 sm:p-4 text-cream hard-shadow-xs flex flex-col justify-between">
          <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider opacity-85">
            Packets Ingested
          </div>
          <div className="my-1.5 sm:my-2">
            <span className="text-2xl sm:text-3xl font-black font-mono-num">
              {metrics ? metrics.packets_received : '--'}
            </span>
          </div>
          <div className="text-[10px] opacity-75 border-t border-cream/30 pt-1">
            ESP32 / Simulator frames
          </div>
        </div>

        {/* Metric 2: Forwarded */}
        <div className="rounded-xl sm:rounded-2xl border-2 border-ink bg-lime p-3 sm:p-4 text-ink hard-shadow-xs flex flex-col justify-between">
          <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider text-ink/75">
            Forwarded Uplink
          </div>
          <div className="my-1.5 sm:my-2">
            <span className="text-2xl sm:text-3xl font-black font-mono-num text-ink">
              {metrics ? metrics.packets_forwarded : '--'}
            </span>
          </div>
          <div className="text-[10px] text-ink/70 border-t border-ink/20 pt-1">
            Persisted in PostgreSQL
          </div>
        </div>

        {/* Metric 3: Current Queue Depth */}
        <div
          className={cn(
            'rounded-xl sm:rounded-2xl border-2 border-ink p-3 sm:p-4 hard-shadow-xs flex flex-col justify-between transition-colors',
            isQueuePending ? 'bg-coral text-cream' : 'bg-mint text-ink'
          )}
        >
          <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider opacity-85">
            Local Queue Depth
          </div>
          <div className="my-1.5 sm:my-2">
            <span className="text-2xl sm:text-3xl font-black font-mono-num">
              {queueSize}
            </span>
          </div>
          <div className="text-[10px] opacity-75 border-t border-current/30 pt-1">
            {isQueuePending ? 'Draining to backend...' : 'Buffer fully synced'}
          </div>
        </div>

        {/* Metric 4: Duplicates Deduplicated */}
        <div className="rounded-xl sm:rounded-2xl border-2 border-ink bg-amber p-3 sm:p-4 text-ink hard-shadow-xs flex flex-col justify-between">
          <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider text-ink/75">
            Duplicate Drops
          </div>
          <div className="my-1.5 sm:my-2">
            <span className="text-2xl sm:text-3xl font-black font-mono-num text-ink">
              {metrics ? metrics.duplicate_packets : 0}
            </span>
          </div>
          <div className="text-[10px] text-ink/70 border-t border-ink/20 pt-1">
            Idempotent sequence dedup
          </div>
        </div>
      </div>

      {/* Resilience Summary Banner */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-cream/90 border border-ink/30 rounded-xl p-2.5 text-[11px] text-ink/80">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
          <span>
            <strong>Zero Data Loss Guarantee:</strong> Ingested packets are durably committed to SQLite before HTTP 202 is acknowledged.
          </span>
        </div>
        <div className="text-[10px] text-ink/60">
          Uptime: {health ? `${Math.floor(health.uptime_seconds)}s` : '--'}
        </div>
      </div>
    </div>
  );
};
