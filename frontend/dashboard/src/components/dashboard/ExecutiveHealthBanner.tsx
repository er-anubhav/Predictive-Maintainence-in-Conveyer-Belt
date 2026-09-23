import React from 'react';
import { Telemetry, Conveyor, SensorNode } from '../../types/api';

interface ExecutiveHealthBannerProps {
  conveyor: Conveyor | null;
  activeNode: SensorNode | null;
  latestTelemetry: Telemetry | null;
  onScenarioTriggered?: () => void;
}

export interface HealthAssessment {
  score: number;
  status: 'Optimal' | 'Attention' | 'Critical';
  badgeBg: string;
  headline: string;
  diagnosis: string;
}

export function evaluateConveyorHealth(t: Telemetry | null): HealthAssessment {
  if (!t) {
    return {
      score: 100,
      status: 'Optimal',
      badgeBg: 'bg-lime text-ink',
      headline: 'Awaiting Sensor Data',
      diagnosis: 'Listening for real-time sensor streams.',
    };
  }

  let deductions = 0;
  let issue = '';
  let isCritical = false;

  // Vibration & Shock
  if (t.vibration_rms > 1.0 || t.vibration_kurtosis > 8.0) {
    deductions += 45;
    isCritical = true;
    issue = `Heavy vibration & impact shock (${t.vibration_rms.toFixed(2)}g, Kurtosis ${t.vibration_kurtosis.toFixed(1)})`;
  } else if (t.vibration_rms > 0.6 || t.vibration_kurtosis > 4.5) {
    deductions += 15;
    issue = `Elevated vibration (${t.vibration_rms.toFixed(2)}g)`;
  }

  // Temperature
  if (t.temperature > 65) {
    deductions += 40;
    isCritical = true;
    issue = `Overheat hazard (${t.temperature.toFixed(1)}°C) — bearing friction`;
  } else if (t.temperature > 50) {
    deductions += 15;
    if (!issue) issue = `Elevated temperature (${t.temperature.toFixed(1)}°C)`;
  }

  // Lateral Tracking Drift
  const drift = Math.abs(t.tracking_position);
  if (drift > 8.0) {
    deductions += 30;
    issue = `Belt drifting off-center (${t.tracking_position > 0 ? '+' : ''}${t.tracking_position.toFixed(1)} mm)`;
  } else if (drift > 4.5) {
    deductions += 10;
    if (!issue) issue = `Minor lateral drift (${t.tracking_position > 0 ? '+' : ''}${t.tracking_position.toFixed(1)} mm)`;
  }

  const score = Math.max(20, 100 - deductions);

  if (isCritical || score < 60) {
    return {
      score,
      status: 'Critical',
      badgeBg: 'bg-white text-coral',
      headline: 'Mechanical Fault Detected',
      diagnosis: issue || 'Sensor readings exceed safe limits.',
    };
  }

  if (deductions > 10 || score < 85) {
    return {
      score,
      status: 'Attention',
      badgeBg: 'bg-white text-amber-700',
      headline: 'Warning: Wear / Drift',
      diagnosis: issue || 'Sensor reading deviating from normal baseline.',
    };
  }

  return {
    score,
    status: 'Optimal',
    badgeBg: 'bg-white text-emerald-700',
    headline: 'All Systems Normal',
    diagnosis: 'Belt running smoothly. No mechanical faults detected.',
  };
}

export const ExecutiveHealthBanner: React.FC<ExecutiveHealthBannerProps> = ({
  conveyor,
  latestTelemetry,
}) => {
  const assessment = evaluateConveyorHealth(latestTelemetry);

  return (
    <div className="rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-ink bg-cream p-5 sm:p-7 sm:pl-8 hard-shadow font-mono text-ink">
      {/* Score + Headline */}
      <div className="flex items-center gap-6 sm:gap-10">
        <div className="grid size-22 sm:size-26 shrink-0 place-items-center rounded-2xl bg-white">
          <div className="text-center">
            <div className="text-4xl sm:text-5xl font-black font-grotesk tracking-tight leading-none text-ink">
              {assessment.score}%
            </div>
            <div className="text-xs sm:text-sm font-black uppercase tracking-wider text-ink/70 mt-1.5">
              Health
            </div>
          </div>
        </div>

        <div className="pl-3 sm:pl-6">
          <div className="flex items-center gap-3.5 sm:gap-4 flex-wrap mb-1.5">
            <span className={`rounded-full border-2 border-ink px-3.5 py-1 text-sm sm:text-base font-black uppercase tracking-wider hard-shadow-xs ${assessment.badgeBg}`}>
              {assessment.status}
            </span>
            <span className="text-sm sm:text-base text-ink/75 font-bold">
              {conveyor?.name || 'Conveyor #01'}
            </span>
          </div>

          <h2 className="font-mono text-xl sm:text-2xl font-bold uppercase tracking-wider text-ink">
            {assessment.headline}
          </h2>

          <p className="text-sm sm:text-base text-ink/85 font-medium mt-1">
            {assessment.diagnosis}
          </p>
        </div>
      </div>
    </div>
  );
};
