import React from 'react';
import { SensorNode } from '../../types/api';
import { Cpu, Radio, Shield, Clock, MapPin } from 'lucide-react';

interface SensorsViewProps {
  sensors: SensorNode[];
  selectedNodeCode: string | null;
  onSelectNode: (code: string) => void;
}

export const SensorsView: React.FC<SensorsViewProps> = ({
  sensors,
  selectedNodeCode,
  onSelectNode,
}) => {
  return (
    <div className="space-y-6 font-mono text-ink">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-coral p-5 hard-shadow text-ink">
        <div className="flex items-center gap-3">
          <div className="grid size-12 place-items-center rounded-2xl border-2 border-ink bg-cream hard-shadow-xs">
            <Cpu className="size-6 stroke-[2.5]" />
          </div>
          <div>
            <h2 className="font-grotesk text-xl font-black uppercase tracking-tight">
              Distributed Sensor Node Fleet
            </h2>
            <p className="text-xs font-mono font-medium text-ink/80">
              Multi-modal edge sensing units deployed along conveyor structures.
            </p>
          </div>
        </div>
        <span className="self-start sm:self-auto rounded-full border-2 border-ink bg-cream px-3 py-1 text-xs font-mono font-black uppercase tracking-wider hard-shadow-xs">
          {sensors.length} Active Nodes
        </span>
      </div>

      {/* Grid of Sensor Nodes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {sensors.map((s) => {
          const isSelected = selectedNodeCode === s.node_code;
          const isOnline = s.status === 'ONLINE';

          return (
            <div
              key={s.id}
              onClick={() => onSelectNode(s.node_code)}
              className={`rounded-2xl border-2 border-ink p-5 transition-all cursor-pointer ${
                isSelected
                  ? 'bg-amber hard-shadow -translate-y-1'
                  : 'bg-cream hard-shadow-sm hover:-translate-y-1 hover:hard-shadow'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className="grid size-10 place-items-center rounded-xl border-2 border-ink bg-cream hard-shadow-xs">
                    <Radio className="w-5 h-5 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="font-grotesk text-base font-black uppercase text-ink">{s.node_code}</h3>
                    <span className="text-[11px] font-mono font-bold text-ink/70">HARDWARE ID #{s.id}</span>
                  </div>
                </div>
                <span
                  className={`rounded-full border-2 border-ink px-2.5 py-0.5 text-[10px] font-mono font-black uppercase tracking-wider flex items-center gap-1 text-ink hard-shadow-xs ${
                    isOnline ? 'bg-lime' : 'bg-sand'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full border border-ink ${isOnline ? 'bg-emerald-600 animate-pulse' : 'bg-neutral-500'}`} />
                  {s.status}
                </span>
              </div>

              <div className="mt-4 space-y-2 text-xs border-t-2 border-ink/20 pt-3">
                <div className="flex justify-between items-center">
                  <span className="text-ink/70 font-bold uppercase flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    Location:
                  </span>
                  <span className="font-black text-ink">{s.location}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-ink/70 font-bold uppercase flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    Firmware:
                  </span>
                  <span className="font-bold text-ink rounded-full border border-ink bg-sand/50 px-2 py-0.5 text-[10px]">
                    {s.firmware_version}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink/70 font-bold uppercase">Conveyor Ref:</span>
                  <span className="font-bold text-ink">Conveyor #{s.conveyor_id}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-ink/70 font-bold uppercase flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Last Active:
                  </span>
                  <span className="font-bold text-ink">
                    {s.last_seen ? new Date(s.last_seen).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t-2 border-ink flex items-center justify-between text-xs font-mono font-black uppercase">
                <span>{isSelected ? 'Currently Selected' : 'Select Sensor Node'}</span>
                <span className="rounded-full border border-ink bg-cream px-2 py-0.5 text-[10px] font-bold">
                  {isSelected ? 'ACTIVE' : 'INSPECT'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
