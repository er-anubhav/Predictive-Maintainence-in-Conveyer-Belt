import React from 'react';
import { Conveyor, SensorNode } from '../../types/api';
import { HelpCircle, Activity, LayoutDashboard, FileText, Layers, Video } from 'lucide-react';
import { ScenarioSwitcher } from '../dashboard/ScenarioSwitcher';

export type NavTab = 'overview' | 'multimodal' | 'sensors' | 'telemetry' | 'conveyors';

interface SiteNavProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onOpenArchitecture: () => void;
  conveyors: Conveyor[];
  selectedConveyorId: number | null;
  onSelectConveyor: (id: number) => void;
  sensorNodes: SensorNode[];
  selectedNodeId: string | null;
  onSelectNode: (code: string) => void;
  activeNode?: SensorNode | null;
  onScenarioTriggered?: () => void;
}

interface TabItem {
  id: NavTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TABS: TabItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'multimodal', label: 'Vision & Evidence', icon: Video },
  { id: 'sensors', label: 'All Sensors', icon: Activity },
  { id: 'telemetry', label: 'Raw Logs', icon: FileText },
  { id: 'conveyors', label: 'Fleet Assets', icon: Layers },
];

export const SiteNav: React.FC<SiteNavProps> = ({
  currentTab,
  onSelectTab,
  onOpenArchitecture,
  conveyors,
  selectedConveyorId,
  onSelectConveyor,
  sensorNodes,
  selectedNodeId,
  onSelectNode,
  activeNode,
  onScenarioTriggered,
}) => {
  return (
    <header className="w-full space-y-4 pb-2 font-mono">
      {/* Top Utility Controls: Left = Interactive Demo, Right = Rig, Node & Architecture */}
      <div className="flex flex-wrap items-center justify-between gap-3 sm:gap-4">
        {/* Top-Left: Interactive Demo Presets */}
        <ScenarioSwitcher
          activeNode={activeNode || null}
          onScenarioTriggered={onScenarioTriggered || (() => {})}
        />

        {/* Top-Right Utility Controls */}
        <div className="flex flex-wrap items-center justify-end gap-3 sm:gap-4">
          {/* Conveyor Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm sm:text-base uppercase text-ink/75">Rig:</span>
          <select
            value={selectedConveyorId || ''}
            onChange={(e) => onSelectConveyor(Number(e.target.value))}
            className="bg-cream border-2 border-ink rounded-xl px-3.5 py-1.5 sm:px-4 sm:py-2 text-sm sm:text-base text-ink focus:outline-none cursor-pointer hard-shadow-xs hover:-translate-y-0.5 transition-transform"
          >
            {conveyors.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Node Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm sm:text-base uppercase text-ink/75">Node:</span>
          <select
            value={selectedNodeId || ''}
            onChange={(e) => onSelectNode(e.target.value)}
            className="bg-cream border-2 border-ink rounded-xl px-3.5 py-1.5 sm:px-4 sm:py-2 text-sm sm:text-base text-ink focus:outline-none cursor-pointer hard-shadow-xs hover:-translate-y-0.5 transition-transform"
          >
            <option value="ALL">All Nodes</option>
            {sensorNodes.map((n) => (
              <option key={n.id} value={n.node_code}>
                {n.node_code}
              </option>
            ))}
          </select>
        </div>

        {/* Architecture Modal Trigger */}
        <button
          onClick={onOpenArchitecture}
          className="flex items-center gap-2 rounded-full border-2 border-ink bg-coral text-cream px-4 sm:px-5 py-2 sm:py-2.5 text-sm sm:text-base uppercase tracking-wider hard-shadow-xs hover:-translate-y-0.5 active:translate-y-0.5 cursor-pointer"
          title="View System Architecture"
        >
          <HelpCircle className="w-5 h-5 stroke-[2.5]" />
          <span>Architecture</span>
        </button>
        </div>
      </div>

      {/* Brand Identity — Centered with Generous Spacing Above and Below */}
      <div className="flex flex-col items-center text-center space-y-2.5 py-6 sm:py-9 my-1">
        <div className="flex items-center justify-center gap-3 sm:gap-4 flex-wrap">
          <span className="size-11 sm:size-14 shrink-0 rounded-full bg-coral outline-3 outline-ink grid place-items-center text-cream hard-shadow-xs">
            <Activity className="size-6 sm:size-8 stroke-[3]" />
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl text-ink">
            Conveyor Health System
          </h1>
        </div>
        <p className="text-xs sm:text-sm md:text-base text-ink/75 font-mono font-bold tracking-wide">
          Continuous Monitoring & Automated Fault Detection
        </p>
      </div>

      {/* Navigation Tabs (Center Aligned) */}
      <div className="flex justify-center pt-1">
        <nav className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
          {TABS.map((tab) => {
            const isActive = currentTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`flex items-center gap-2.5 rounded-full border-2 border-ink px-5 sm:px-6 py-2.5 sm:py-3 font-mono text-sm sm:text-base font-black uppercase tracking-wider transition-all cursor-pointer ${
                  isActive
                    ? 'bg-lime text-ink hard-shadow-xs translate-x-[1px] translate-y-[1px]'
                    : 'bg-white text-ink hover:-translate-y-0.5 active:translate-y-0.5 hard-shadow-xs'
                }`}
              >
                <Icon className="size-5 stroke-[2.5]" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
