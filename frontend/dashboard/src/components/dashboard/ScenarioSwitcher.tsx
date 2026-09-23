import React, { useState } from 'react';
import { SensorNode } from '../../types/api';
import { api } from '../../services/api';
import {
  CheckCircle2,
  AlertTriangle,
  Activity,
  Flame,
  Camera,
  Layers,
} from 'lucide-react';

export interface ScenarioPreset {
  id: string;
  label: string;
  tag: string;
  badgeBg: string;
  icon: React.ReactNode;
  cameraScenario: string;
  payload: {
    vibration: {
      rms: number;
      peak: number;
      kurtosis: number;
      crest_factor: number;
      dominant_frequency_hz: number;
      spectral_energy: number;
    };
    acoustic: { rms: number };
    temperature: number;
    belt_speed: number;
    load: number;
    tracking_position: number;
  };
}

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    id: 'normal',
    label: 'Normal Operation',
    tag: 'Baseline',
    badgeBg: 'bg-lime text-ink',
    icon: <CheckCircle2 className="size-4 text-emerald-800 stroke-[3]" />,
    cameraScenario: 'NORMAL',
    payload: {
      vibration: {
        rms: 0.38,
        peak: 0.95,
        kurtosis: 3.1,
        crest_factor: 2.5,
        dominant_frequency_hz: 14.5,
        spectral_energy: 48.2,
      },
      acoustic: { rms: 0.42 },
      temperature: 41.8,
      belt_speed: 2.82,
      load: 76.5,
      tracking_position: 0.4,
    },
  },
  {
    id: 'bearing_shock',
    label: 'Bearing Anomaly',
    tag: 'Impulsive',
    badgeBg: 'bg-amber text-ink',
    icon: <Activity className="size-4 text-amber-800 stroke-[3]" />,
    cameraScenario: 'NORMAL',
    payload: {
      vibration: {
        rms: 1.85,
        peak: 4.85,
        kurtosis: 16.5,
        crest_factor: 5.65,
        dominant_frequency_hz: 38.0,
        spectral_energy: 245.0,
      },
      acoustic: { rms: 2.95 },
      temperature: 52.0,
      belt_speed: 2.75,
      load: 78.0,
      tracking_position: -1.2,
    },
  },
  {
    id: 'belt_drift',
    label: 'Belt Misalignment',
    tag: 'Edge Wander',
    badgeBg: 'bg-[#ffcc4e] text-ink',
    icon: <AlertTriangle className="size-4 text-amber-900 stroke-[3]" />,
    cameraScenario: 'MISALIGNMENT',
    payload: {
      vibration: {
        rms: 0.55,
        peak: 1.35,
        kurtosis: 3.9,
        crest_factor: 2.45,
        dominant_frequency_hz: 9.0,
        spectral_energy: 68.0,
      },
      acoustic: { rms: 0.5 },
      temperature: 46.5,
      belt_speed: 2.70,
      load: 74.0,
      tracking_position: 16.5,
    },
  },
  {
    id: 'hot_roller',
    label: 'Thermal Event',
    tag: 'Friction',
    badgeBg: 'bg-coral text-cream',
    icon: <Flame className="size-4 text-rose-800 stroke-[3]" />,
    cameraScenario: 'NORMAL',
    payload: {
      vibration: {
        rms: 0.72,
        peak: 1.65,
        kurtosis: 5.1,
        crest_factor: 2.8,
        dominant_frequency_hz: 26.0,
        spectral_energy: 95.0,
      },
      acoustic: { rms: 1.2 },
      temperature: 82.5,
      belt_speed: 2.65,
      load: 82.0,
      tracking_position: 3.5,
    },
  },
  {
    id: 'visible_damage',
    label: 'Visible Belt Damage',
    tag: 'Optical Tear',
    badgeBg: 'bg-rose text-white',
    icon: <Camera className="size-4 text-rose-900 stroke-[3]" />,
    cameraScenario: 'VISIBLE_DAMAGE',
    payload: {
      vibration: {
        rms: 1.45,
        peak: 3.80,
        kurtosis: 11.2,
        crest_factor: 4.2,
        dominant_frequency_hz: 22.0,
        spectral_energy: 180.0,
      },
      acoustic: { rms: 2.1 },
      temperature: 48.0,
      belt_speed: 2.60,
      load: 70.0,
      tracking_position: -2.0,
    },
  },
  {
    id: 'multimodal_event',
    label: 'Multimodal Event',
    tag: 'Compound',
    badgeBg: 'bg-purple-900 text-white',
    icon: <Layers className="size-4 text-purple-300 stroke-[3]" />,
    cameraScenario: 'VISIBLE_DAMAGE',
    payload: {
      vibration: {
        rms: 2.10,
        peak: 5.80,
        kurtosis: 19.0,
        crest_factor: 6.0,
        dominant_frequency_hz: 42.0,
        spectral_energy: 290.0,
      },
      acoustic: { rms: 3.20 },
      temperature: 85.0,
      belt_speed: 2.50,
      load: 88.0,
      tracking_position: 18.5,
    },
  },
];

let globalSeq = 60000;

interface ScenarioSwitcherProps {
  activeNode: SensorNode | null;
  onScenarioTriggered: () => void;
}

export const ScenarioSwitcher: React.FC<ScenarioSwitcherProps> = ({
  activeNode,
  onScenarioTriggered,
}) => {
  const [activePresetId, setActivePresetId] = useState<string>('normal');
  const [isInjecting, setIsInjecting] = useState<boolean>(false);

  const injectScenario = async (preset: ScenarioPreset) => {
    setActivePresetId(preset.id);
    setIsInjecting(true);
    globalSeq += 1;

    try {
      // 1. Trigger camera snapshot with scenario
      await api.triggerCameraSnapshot(preset.cameraScenario).catch(() => null);

      // 2. Transmit through real backend API (evaluates IF-v0.3.1 + Thermal + Tracking + Fusion)
      const packet = {
        sensor_node_id: activeNode?.node_code || 'NODE-001',
        conveyor_id: 'Conveyor-01',
        timestamp: new Date().toISOString(),
        sequence: globalSeq,
        vibration_rms: preset.payload.vibration.rms,
        vibration_peak: preset.payload.vibration.peak,
        vibration_kurtosis: preset.payload.vibration.kurtosis,
        crest_factor: preset.payload.vibration.crest_factor,
        dominant_frequency_hz: preset.payload.vibration.dominant_frequency_hz,
        spectral_energy: preset.payload.vibration.spectral_energy,
        acoustic_rms: preset.payload.acoustic.rms,
        temperature: preset.payload.temperature,
        belt_speed: preset.payload.belt_speed,
        load: preset.payload.load,
        tracking_position: preset.payload.tracking_position,
        source: 'SIMULATED',
      };

      await fetch('/api/v1/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(packet),
      });

      setTimeout(() => {
        onScenarioTriggered();
        setIsInjecting(false);
      }, 300);
    } catch (err) {
      console.warn('Scenario injection failed:', err);
      setIsInjecting(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm sm:text-base uppercase text-ink/75 font-mono">Demo:</span>
      <select
        value={activePresetId}
        disabled={isInjecting}
        onChange={(e) => {
          const preset = SCENARIO_PRESETS.find((p) => p.id === e.target.value);
          if (preset) injectScenario(preset);
        }}
        className="bg-cream border-2 border-ink rounded-xl px-3.5 py-1.5 sm:px-4 sm:py-2 text-sm sm:text-base text-ink focus:outline-none cursor-pointer hard-shadow-xs hover:-translate-y-0.5 transition-transform font-mono"
      >
        {SCENARIO_PRESETS.map((preset) => (
          <option key={preset.id} value={preset.id}>
            {preset.label}
          </option>
        ))}
      </select>
    </div>
  );
};
