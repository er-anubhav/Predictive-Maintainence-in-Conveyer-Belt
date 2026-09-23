import React from 'react';
import { Conveyor, ConveyorDetail } from '../../types/api';
import { Layers, CheckCircle2, ChevronRight, HardDrive } from 'lucide-react';

interface ConveyorsViewProps {
  conveyors: Conveyor[];
  selectedConveyorDetail: ConveyorDetail | null;
  onSelectConveyor: (id: number) => void;
}

export const ConveyorsView: React.FC<ConveyorsViewProps> = ({
  conveyors,
  selectedConveyorDetail,
  onSelectConveyor,
}) => {
  return (
    <div className="space-y-6 font-mono text-ink">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-white p-5 sm:p-6 hard-shadow text-ink">
        <div className="flex items-center gap-3.5">
          <div className="grid size-14 place-items-center rounded-2xl border-2 border-ink bg-cream hard-shadow-xs">
            <Layers className="size-7 stroke-[2.5]" />
          </div>
          <div>
            <h2 className="font-grotesk text-2xl font-black uppercase tracking-tight text-ink">
              Mine Conveyor Asset Fleet
            </h2>
            <p className="text-sm sm:text-base font-mono font-medium text-ink/75 mt-0.5">
              Registered bulk material conveyor systems in the active iron ore mine sector.
            </p>
          </div>
        </div>
        <span className="self-start sm:self-auto rounded-full border-2 border-ink bg-cream px-3.5 py-1.5 text-xs sm:text-sm font-mono font-black uppercase tracking-wider hard-shadow-xs text-ink">
          {conveyors.length} Conveyors Registered
        </span>
      </div>

      {/* Grid of Conveyors */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {conveyors.map((c) => {
          const isSelected = selectedConveyorDetail?.id === c.id;
          return (
            <div
              key={c.id}
              onClick={() => onSelectConveyor(c.id)}
              className={`rounded-2xl border-2 sm:border-3 border-ink p-5 sm:p-6 transition-all cursor-pointer bg-white ${
                isSelected
                  ? 'hard-shadow -translate-y-1.5 ring-2 ring-ink'
                  : 'hard-shadow-sm hover:-translate-y-1 hover:hard-shadow'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className={`grid size-12 place-items-center rounded-xl border-2 border-ink hard-shadow-xs ${isSelected ? 'bg-lime text-ink' : 'bg-white text-ink'}`}>
                    <HardDrive className="w-6 h-6 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="font-grotesk text-lg sm:text-xl font-bold uppercase text-ink">{c.name}</h3>
                    <span className="text-xs sm:text-sm font-mono font-medium text-ink/70">Asset ID #{c.id}</span>
                  </div>
                </div>
                <span className="rounded-full border-2 border-ink bg-lime px-3 py-1 text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 text-ink hard-shadow-xs">
                  <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.5]" />
                  <span>{c.status.toLowerCase() === 'operational' ? 'Operational' : c.status}</span>
                </span>
              </div>

              <div className="mt-4 space-y-2.5 text-sm sm:text-base border-t-2 border-ink/20 pt-3.5">
                <div className="flex justify-between">
                  <span className="text-ink/70 font-medium">Belt Spec:</span>
                  <span className="font-bold text-ink">{c.belt_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink/70 font-medium">Length:</span>
                  <span className="font-bold text-ink">{c.length} m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink/70 font-medium">Width:</span>
                  <span className="font-bold text-ink">{c.width} m</span>
                </div>
              </div>

              <div className="mt-4 pt-3.5 border-t-2 border-ink/20 flex items-center justify-between text-xs sm:text-sm font-mono font-bold">
                <span className={isSelected ? 'text-ink font-bold' : 'text-ink/75'}>
                  {isSelected ? '✓ Currently Selected' : 'Inspect Conveyor'}
                </span>
                <div className={`grid size-7 place-items-center rounded-full border-2 border-ink ${isSelected ? 'bg-lime' : 'bg-white'}`}>
                  <ChevronRight className="w-4 h-4 stroke-[3]" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
