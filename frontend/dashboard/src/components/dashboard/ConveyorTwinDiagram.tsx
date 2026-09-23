import React from 'react';
import { Telemetry, Conveyor, SensorNode } from '../../types/api';
import { Activity, Thermometer, Gauge, MoveHorizontal } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConveyorTwinDiagramProps {
  conveyor?: Conveyor | null;
  activeNode?: SensorNode | null;
  latestTelemetry: Telemetry | null;
}

export const ConveyorTwinDiagram: React.FC<ConveyorTwinDiagramProps> = ({
  latestTelemetry,
}) => {
  const isVibAlert = latestTelemetry ? latestTelemetry.vibration_rms > 0.6 || latestTelemetry.vibration_kurtosis > 6.0 : false;
  const isTempAlert = latestTelemetry ? latestTelemetry.temperature > 50 : false;
  const isDriftAlert = latestTelemetry ? Math.abs(latestTelemetry.tracking_position) > 4.5 : false;
  const isSpeedSlow = latestTelemetry ? latestTelemetry.belt_speed < 2.2 : false;

  const beltSpeed = latestTelemetry ? latestTelemetry.belt_speed : 2.82;
  const tempVal = latestTelemetry ? latestTelemetry.temperature.toFixed(1) : '41.8';
  const driftVal = latestTelemetry ? latestTelemetry.tracking_position.toFixed(1) : '0.4';
  const vibVal = latestTelemetry ? latestTelemetry.vibration_rms.toFixed(2) : '0.38';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* CARD 1: VIBRATION */}
        <div
          className={cn(
            'rounded-2xl border-2 border-ink p-5 hard-shadow transition-all sm:rounded-3xl',
            isVibAlert ? 'bg-coral text-cream' : 'bg-[#ffcc4e] text-ink'
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid size-12 sm:size-14 shrink-0 place-items-center rounded-xl bg-white border-2 border-ink text-ink hard-shadow-xs">
                <Activity className="size-6 sm:size-7 stroke-[2.5]" />
              </span>
              <div>
                <p className="font-grotesk text-lg sm:text-xl font-bold uppercase leading-tight">
                  Vibration
                </p>
                <p className={cn('font-mono text-sm sm:text-base uppercase font-medium mt-0.5', isVibAlert ? 'text-cream/90' : 'text-ink/75')}>
                  Tri-Axial Energy
                </p>
              </div>
            </div>
            <span
              className={cn(
                'rounded-full border border-ink px-3 py-1 font-mono text-xs sm:text-sm font-bold uppercase',
                isVibAlert ? 'bg-white text-coral' : 'bg-white text-emerald-700'
              )}
            >
              {isVibAlert ? 'Alert' : 'Normal'}
            </span>
          </div>

          <div className="mt-4 sm:mt-5 flex items-baseline gap-2.5">
            <span className="text-5xl sm:text-6xl font-bold font-grotesk tracking-tight tabular-nums">
              {vibVal}
            </span>
            <span className="font-mono text-base sm:text-lg font-bold uppercase opacity-85">g RMS</span>
          </div>

          {/* Dynamic Waveform SVG */}
          <div className="mt-4 sm:mt-5 flex h-11 w-full items-center justify-between rounded-xl bg-white px-3.5 border border-ink shadow-inner overflow-hidden">
            <svg viewBox="0 0 160 28" className="h-full w-full" preserveAspectRatio="none">
              <path
                d={
                  isVibAlert
                    ? 'M 0 14 L 15 14 L 25 3 L 35 25 L 45 4 L 55 24 L 65 14 L 85 14 L 95 2 L 105 26 L 115 5 L 125 23 L 135 14 L 160 14'
                    : 'M 0 14 Q 20 6, 40 14 T 80 14 T 120 14 T 160 14'
                }
                fill="none"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-pulse"
              />
            </svg>
            <span className="font-mono text-xs sm:text-sm font-bold uppercase ml-2 shrink-0 text-ink/75">
              {isVibAlert ? 'Spike' : '1 kHz'}
            </span>
          </div>
        </div>

        {/* CARD 2: TEMPERATURE */}
        <div
          className={cn(
            'rounded-2xl border-2 border-ink p-5 hard-shadow transition-all sm:rounded-3xl',
            isTempAlert ? 'bg-coral text-cream' : 'bg-mint text-ink'
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid size-12 sm:size-14 shrink-0 place-items-center rounded-xl bg-white border-2 border-ink text-ink hard-shadow-xs">
                <Thermometer className="size-6 sm:size-7 stroke-[2.5]" />
              </span>
              <div>
                <p className="font-grotesk text-lg sm:text-xl font-bold uppercase leading-tight">
                  Temperature
                </p>
                <p className={cn('font-mono text-sm sm:text-base uppercase font-medium mt-0.5', isTempAlert ? 'text-cream/90' : 'text-ink/75')}>
                  Bearing Shell
                </p>
              </div>
            </div>
            <span
              className={cn(
                'rounded-full border border-ink px-3 py-1 font-mono text-xs sm:text-sm font-bold uppercase',
                isTempAlert ? 'bg-white text-coral' : 'bg-white text-emerald-700'
              )}
            >
              {isTempAlert ? 'Hot' : 'Safe'}
            </span>
          </div>

          <div className="mt-4 sm:mt-5 flex items-baseline gap-2.5">
            <span className="text-5xl sm:text-6xl font-bold font-grotesk tracking-tight tabular-nums">
              {tempVal}
            </span>
            <span className="font-mono text-base sm:text-lg font-bold uppercase opacity-85">°C</span>
          </div>

          {/* Dynamic Waveform SVG */}
          <div className="mt-4 sm:mt-5 flex h-11 w-full items-center justify-between rounded-xl bg-white px-3.5 border border-ink shadow-inner overflow-hidden">
            <svg viewBox="0 0 160 28" className="h-full w-full" preserveAspectRatio="none">
              <path
                d="M 0 18 C 20 18, 35 8, 55 12 C 75 16, 95 6, 115 14 C 135 22, 145 10, 160 14"
                fill="none"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="animate-pulse"
              />
            </svg>
            <span className="font-mono text-xs sm:text-sm font-bold uppercase ml-2 shrink-0 text-ink/75">
              PT100
            </span>
          </div>
        </div>

        {/* CARD 3: BELT SPEED */}
        <div
          className={cn(
            'rounded-2xl border-2 border-ink p-5 hard-shadow transition-all sm:rounded-3xl',
            isSpeedSlow ? 'bg-amber text-ink' : 'bg-lime text-ink'
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid size-12 sm:size-14 shrink-0 place-items-center rounded-xl bg-white border-2 border-ink text-ink hard-shadow-xs">
                <Gauge className="size-6 sm:size-7 stroke-[2.5]" />
              </span>
              <div>
                <p className="font-grotesk text-lg sm:text-xl font-bold uppercase leading-tight">
                  Belt Speed
                </p>
                <p className="font-mono text-sm sm:text-base uppercase font-medium text-ink/75 mt-0.5">
                  Drive Pulley
                </p>
              </div>
            </div>
            <span
              className={cn(
                'rounded-full border border-ink px-3 py-1 font-mono text-xs sm:text-sm font-bold uppercase',
                isSpeedSlow ? 'bg-white text-coral' : 'bg-white text-emerald-700'
              )}
            >
              {isSpeedSlow ? 'Slow' : 'Nominal'}
            </span>
          </div>

          <div className="mt-4 sm:mt-5 flex items-baseline gap-2.5">
            <span className="text-5xl sm:text-6xl font-bold font-grotesk tracking-tight tabular-nums">
              {beltSpeed.toFixed(2)}
            </span>
            <span className="font-mono text-base sm:text-lg font-bold uppercase opacity-85">m/s</span>
          </div>

          {/* Dynamic Waveform SVG */}
          <div className="mt-4 sm:mt-5 flex h-11 w-full items-center justify-between rounded-xl bg-white px-3.5 border border-ink shadow-inner overflow-hidden">
            <svg viewBox="0 0 160 28" className="h-full w-full" preserveAspectRatio="none">
              <path
                d="M 0 14 L 20 14 L 30 6 L 40 22 L 50 14 L 80 14 L 90 6 L 100 22 L 110 14 L 160 14"
                fill="none"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="animate-pulse"
              />
            </svg>
            <span className="font-mono text-xs sm:text-sm font-bold uppercase ml-2 shrink-0 text-ink/75">
              Tacho
            </span>
          </div>
        </div>

        {/* CARD 4: TRACKING / ALIGNMENT */}
        <div
          className={cn(
            'rounded-2xl border-2 border-ink p-5 hard-shadow transition-all sm:rounded-3xl',
            isDriftAlert ? 'bg-coral text-cream ring-2 ring-coral' : 'bg-[#ffcc4e] text-ink'
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid size-12 sm:size-14 shrink-0 place-items-center rounded-xl bg-white border-2 border-ink text-ink hard-shadow-xs">
                <MoveHorizontal className="size-6 sm:size-7 stroke-[2.5]" />
              </span>
              <div>
                <p className="font-grotesk text-lg sm:text-xl font-bold uppercase leading-tight">
                  Alignment
                </p>
                <p className={cn('font-mono text-sm sm:text-base uppercase font-medium mt-0.5', isDriftAlert ? 'text-cream/90' : 'text-ink/75')}>
                  Edge Position
                </p>
              </div>
            </div>
            <span
              className={cn(
                'rounded-full border border-ink px-3 py-1 font-mono text-xs sm:text-sm font-bold uppercase',
                isDriftAlert ? 'bg-white text-coral' : 'bg-white text-emerald-700'
              )}
            >
              {isDriftAlert ? 'Drift' : 'Center'}
            </span>
          </div>

          <div className="mt-4 sm:mt-5 flex items-baseline gap-2.5">
            <span className="text-5xl sm:text-6xl font-bold font-grotesk tracking-tight tabular-nums">
              {Number(driftVal) > 0 ? `+${driftVal}` : driftVal}
            </span>
            <span className="font-mono text-base sm:text-lg font-bold uppercase opacity-85">mm</span>
          </div>

          {/* Center-alignment track bar */}
          <div className="mt-4 sm:mt-5 flex h-11 w-full items-center justify-between rounded-xl bg-white px-3.5 border border-ink shadow-inner overflow-hidden relative">
            <div className="w-0.5 h-full bg-ink/40 absolute left-1/2 -translate-x-1/2" />
            <div
              className={`size-4 rounded-full border-2 border-ink hard-shadow-xs transition-all ${
                isDriftAlert ? 'bg-coral translate-x-8' : 'bg-lime translate-x-0'
              }`}
              style={{
                marginLeft: `calc(50% + ${Math.min(35, Math.max(-35, Number(driftVal) * 3.5))}px - 8px)`,
              }}
            />
            <span className="font-mono text-xs sm:text-sm font-bold uppercase text-ink/75 z-10">
              {isDriftAlert ? 'Off-Center' : 'Aligned'}
            </span>
          </div>
        </div>
      </div>
  );
};
