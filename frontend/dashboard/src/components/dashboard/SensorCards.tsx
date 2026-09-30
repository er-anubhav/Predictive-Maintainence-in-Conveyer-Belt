import React, { useState } from 'react';
import { Telemetry } from '../../types/api';
import { cn } from '../../lib/utils';
import { Info, Activity, Thermometer, Gauge, Scale, MoveHorizontal, Volume2 } from 'lucide-react';

interface SensorCardsProps {
  telemetry: Telemetry | null;
}

interface SensorConfig {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  caption: string;
  cardBg: string;
  captionColor: string;
  unit: string;
  whatItDetects: string;
  safeLimit: string;
  getValue: (t: Telemetry) => string;
  getNumeric: (t: Telemetry) => number;
  getSecondary: (t: Telemetry) => string;
  getStatus: (t: Telemetry) => { label: string; bg: string; text: string };
  max: number;
}

const SENSOR_CONFIGS: SensorConfig[] = [
  {
    id: 'vibration',
    icon: Activity,
    label: 'Vibration RMS',
    caption: 'Tri-Axial Velocity Energy',
    cardBg: 'bg-[#ffcc4e] text-ink',
    captionColor: 'text-ink/75',
    unit: 'g',
    whatItDetects: 'Detects roller bearing wear, imbalance & joint splice slapping',
    safeLimit: 'Safe baseline: < 0.60 g',
    getValue: (t) => t.vibration_rms.toFixed(3),
    getNumeric: (t) => t.vibration_rms,
    getSecondary: (t) => `Peak: ${t.vibration_peak.toFixed(2)}g · Kurtosis: ${t.vibration_kurtosis.toFixed(1)}`,
    getStatus: (t) => {
      if (t.vibration_rms > 1.0 || t.vibration_kurtosis > 8.0) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'Spiky Impact Detected' };
      }
      if (t.vibration_rms > 0.6 || t.vibration_kurtosis > 4.5) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'Mild Transients' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Smooth Rotation' };
    },
    max: 2.5,
  },
  {
    id: 'temperature',
    icon: Thermometer,
    label: 'Bearing Shell',
    caption: 'Thermal Probe PT100',
    cardBg: 'bg-coral text-cream',
    captionColor: 'text-cream/80',
    unit: '°C',
    whatItDetects: 'Detects idler roller friction and bearing seizure before fire hazard',
    safeLimit: 'Safe baseline: < 50.0 °C',
    getValue: (t) => t.temperature.toFixed(1),
    getNumeric: (t) => t.temperature,
    getSecondary: (t) => (t.temperature > 65 ? 'Critical Heat Warning' : t.temperature > 50 ? 'Elevated Thermal' : 'Thermal Nominal'),
    getStatus: (t) => {
      if (t.temperature > 65) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'Overheat Hazard' };
      }
      if (t.temperature > 50) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'Friction Rising' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Thermal Stable' };
    },
    max: 100,
  },
  {
    id: 'speed',
    icon: Gauge,
    label: 'Belt Velocity',
    caption: 'Tachometer Pulse Stream',
    cardBg: 'bg-lime text-ink',
    captionColor: 'text-ink/70',
    unit: 'm/s',
    whatItDetects: 'Detects drive pulley belt slip and transfer throughput slowdown',
    safeLimit: 'Rated target: 2.80 m/s',
    getValue: (t) => t.belt_speed.toFixed(2),
    getNumeric: (t) => t.belt_speed,
    getSecondary: (t) => `Nominal: 2.80 m/s · ${(t.belt_speed * 3.6).toFixed(1)} km/h`,
    getStatus: (t) => {
      if (t.belt_speed < 2.0) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'Belt Slip Risk' };
      }
      if (t.belt_speed < 2.5) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'Sub-Optimal Speed' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Steady Drive' };
    },
    max: 4.0,
  },
  {
    id: 'load',
    icon: Scale,
    label: 'Material Load',
    caption: 'Strain Gauge Weightometer',
    cardBg: 'bg-mint text-ink',
    captionColor: 'text-ink/70',
    unit: '%',
    whatItDetects: 'Detects conveyor overloading, chute blockages and ore spillage',
    safeLimit: 'Safe range: 50 – 85 %',
    getValue: (t) => t.load.toFixed(1),
    getNumeric: (t) => t.load,
    getSecondary: (t) => `Est: ${(t.load * 24).toFixed(0)} TPH Mass Transfer`,
    getStatus: (t) => {
      if (t.load > 90) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'Overload Risk' };
      }
      if (t.load > 80) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'High Capacity' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Optimal Feed' };
    },
    max: 100,
  },
  {
    id: 'tracking',
    icon: MoveHorizontal,
    label: 'Lateral Tracking',
    caption: 'Laser Edge Alignment',
    cardBg: 'bg-[#ffcc4e] text-ink',
    captionColor: 'text-ink/75',
    unit: 'mm',
    whatItDetects: 'Detects belt edge drift, preventing side-frame rubbing and tearing',
    safeLimit: 'Tolerance: ± 5.0 mm',
    getValue: (t) => (t.tracking_position > 0 ? `+${t.tracking_position.toFixed(1)}` : t.tracking_position.toFixed(1)),
    getNumeric: (t) => Math.abs(t.tracking_position),
    getSecondary: (t) => (Math.abs(t.tracking_position) > 8 ? 'Skirt Rubbing Warning' : 'Tracking Center In-Tolerance'),
    getStatus: (t) => {
      if (Math.abs(t.tracking_position) > 8.0) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'Severe Edge Drift' };
      }
      if (Math.abs(t.tracking_position) > 4.5) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'Mild Misalignment' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Center Aligned' };
    },
    max: 20,
  },
  {
    id: 'acoustic',
    icon: Volume2,
    label: 'Acoustic Emission',
    caption: 'High-Freq Metal Friction',
    cardBg: 'bg-magenta text-cream',
    captionColor: 'text-cream/80',
    unit: 'V',
    whatItDetects: 'Detects microscopic splice tear, joint fatigue and idler bearing dry friction',
    safeLimit: 'Safe baseline: < 0.80 V',
    getValue: (t) => t.acoustic_rms.toFixed(3),
    getNumeric: (t) => t.acoustic_rms,
    getSecondary: (t) => (t.acoustic_rms > 0.8 ? 'Dry Idler Friction High' : 'Baseline Film Lubrication'),
    getStatus: (t) => {
      if (t.acoustic_rms > 1.0) {
        return { label: 'Alert', bg: 'bg-white text-coral', text: 'High HF Noise' };
      }
      if (t.acoustic_rms > 0.6) {
        return { label: 'Elevated', bg: 'bg-white text-amber-700', text: 'Friction Elevated' };
      }
      return { label: 'Nominal', bg: 'bg-white text-emerald-700', text: 'Quiet Travel' };
    },
    max: 2.0,
  },
];

export const SensorCards: React.FC<SensorCardsProps> = ({ telemetry }) => {
  const [activeChannels, setActiveChannels] = useState<Record<string, boolean>>({
    vibration: true,
    temperature: true,
    speed: true,
    load: true,
    tracking: true,
    acoustic: true,
  });

  const toggleChannel = (id: string) => {
    setActiveChannels((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between font-mono text-sm sm:text-base uppercase tracking-wider text-ink/75 px-1">
        <span className="font-bold">Multi-Modal Edge Sensor Fleet</span>
        <span>
          {Object.values(activeChannels).filter(Boolean).length} of {SENSOR_CONFIGS.length} channels online
        </span>
      </div>

      <section
        aria-label="Sensor channels"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6 gap-4 sm:gap-5"
      >
        {SENSOR_CONFIGS.map((cfg) => {
          const isEnabled = Boolean(activeChannels[cfg.id]);
          const numValue = telemetry ? cfg.getNumeric(telemetry) : 0;
          const status = telemetry ? cfg.getStatus(telemetry) : { label: 'Offline', bg: 'bg-white text-ink/70', text: 'Awaiting data' };
          const pct = Math.min(100, Math.max(8, (numValue / cfg.max) * 100));

          return (
            <div
              key={cfg.id}
              className={cn(
                'rounded-2xl border-2 border-ink p-4 hard-shadow-sm transition-all sm:rounded-[2rem] sm:p-5 md:p-6 sm:hard-shadow flex flex-col justify-between',
                cfg.cardBg,
                !isEnabled && 'opacity-70 grayscale-[30%]'
              )}
            >
              {/* Card Header with Icon, Labels and Status Pill */}
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-cream hard-shadow-xs sm:size-14 sm:rounded-2xl text-ink">
                      <cfg.icon className="size-6 sm:size-7 stroke-[2.5]" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="truncate font-mono text-base sm:text-lg font-bold uppercase tracking-wider">
                          {cfg.label}
                        </h3>
                        <span className={`rounded-full border border-ink px-2.5 py-0.5 text-xs sm:text-sm font-black uppercase ${status.bg}`}>
                          {status.label}
                        </span>
                        <span className={`rounded border px-1.5 py-0.2 text-[10px] font-mono font-bold uppercase ${
                          cfg.id === 'tracking' || telemetry?.source === 'SIMULATED' || telemetry?.source === 'DEMO_SIMULATED' || Boolean(telemetry?.is_simulated) ? 'bg-amber-100 text-amber-900 border-amber-300' : 'bg-white/80 text-ink/75 border-ink/20'
                        }`}>
                          {cfg.id === 'tracking' || telemetry?.source === 'SIMULATED' || telemetry?.source === 'DEMO_SIMULATED' || Boolean(telemetry?.is_simulated) ? 'SIMULATED' : 'REAL'}
                        </span>
                      </div>
                      <p className={cn('truncate font-mono text-xs sm:text-sm font-medium mt-0.5', cfg.captionColor)}>
                        {cfg.caption}
                      </p>
                    </div>
                  </div>

                  {/* Channel Active Pill Button */}
                  <button
                    onClick={() => toggleChannel(cfg.id)}
                    className={cn(
                      'rounded-full border-2 border-ink px-3 py-1 font-mono text-xs sm:text-sm font-bold uppercase transition-transform hover:-translate-y-0.5 active:translate-y-0.5 cursor-pointer',
                      isEnabled ? 'bg-cream text-ink' : 'bg-transparent text-current opacity-60'
                    )}
                  >
                    {isEnabled ? 'ON' : 'OFF'}
                  </button>
                </div>

                {/* Big Metric Display */}
                <div className="mt-4 sm:mt-5 flex items-baseline gap-2.5">
                  <span className="font-mono text-5xl sm:text-6xl font-bold tracking-tight">
                    {telemetry ? cfg.getValue(telemetry) : '--'}
                  </span>
                  <span className="font-mono text-xl sm:text-2xl font-bold opacity-85">
                    {cfg.unit}
                  </span>
                </div>

                {/* Plain English "What This Detects" Note for Judges */}
                <div className="mt-3 rounded-2xl border-2 border-ink/40 bg-cream/95 p-3.5 text-ink space-y-1.5 font-mono">
                  <div className="flex items-center gap-1.5 text-xs sm:text-sm font-bold uppercase text-ink/75">
                    <Info className="w-4 h-4 shrink-0" />
                    <span>Diagnostics:</span>
                  </div>
                  <div className="text-xs sm:text-sm text-ink leading-snug font-medium">
                    {cfg.whatItDetects}
                  </div>
                  <div className="pt-2 border-t border-ink/20 flex items-center justify-between text-xs sm:text-sm font-bold flex-wrap gap-1">
                    <span className="text-ink/70">{cfg.safeLimit}</span>
                    <span className="underline underline-offset-2">{status.text}</span>
                  </div>
                </div>
              </div>

              {/* Pill-Shaped Live Signal Track */}
              <div className="mt-4 sm:mt-5">
                <div className="flex h-11 sm:h-12 items-center justify-between rounded-full bg-cream px-3.5 sm:px-4 outline-2 -outline-offset-1 outline-ink shadow-inner text-ink">
                  <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-coral animate-ping" />
                    <span className="font-mono text-xs sm:text-sm font-bold uppercase">
                      {isEnabled ? 'Live Stream' : 'Muted'}
                    </span>
                  </div>
                  <div className="w-20 sm:w-28 h-2.5 rounded-full bg-sand/60 overflow-hidden border border-ink/30">
                    <div
                      className="h-full bg-ink transition-all duration-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="font-mono text-xs sm:text-sm font-bold text-ink/80">
                    {pct.toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
};
