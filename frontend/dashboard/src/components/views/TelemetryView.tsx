import React from 'react';
import { Telemetry } from '../../types/api';
import { TelemetryTable } from '../dashboard/TelemetryTable';
import { Radio, Activity } from 'lucide-react';

interface TelemetryViewProps {
  telemetryList: Telemetry[];
  sensorCode: string;
}

export const TelemetryView: React.FC<TelemetryViewProps> = ({ telemetryList, sensorCode }) => {
  return (
    <div className="space-y-6 font-mono text-ink">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-lime p-5 hard-shadow text-ink">
        <div className="flex items-center gap-3">
          <div className="grid size-12 place-items-center rounded-2xl border-2 border-ink bg-cream hard-shadow-xs">
            <Radio className="size-6 stroke-[2.5]" />
          </div>
          <div>
            <h2 className="font-grotesk text-xl font-black uppercase tracking-tight">
              Telemetry Stream Inspector
            </h2>
            <p className="text-xs font-mono font-medium text-ink/80">
              Raw ingested metrics time series for Node <strong className="text-ink underline">{sensorCode}</strong>.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full border-2 border-ink bg-cream px-3.5 py-1 text-xs font-mono font-black uppercase tracking-wider hard-shadow-xs">
          <Activity className="w-4 h-4 text-emerald-600 stroke-[3]" />
          <span>Live Buffer: {telemetryList.length} Packets</span>
        </div>
      </div>

      {/* Embedded Telemetry Table */}
      <TelemetryTable telemetryList={telemetryList} sensorCode={sensorCode} />
    </div>
  );
};
