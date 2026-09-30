import { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { Conveyor, ConveyorDetail, SensorNode, Telemetry } from './types/api';
import { SiteNav, NavTab } from './components/layout/SiteNav';
import { ExecutiveHealthBanner } from './components/dashboard/ExecutiveHealthBanner';
import { ConveyorTwinDiagram } from './components/dashboard/ConveyorTwinDiagram';
import { ArchitectureModal } from './components/layout/ArchitectureModal';
import { SensorCards } from './components/dashboard/SensorCards';
import { TelemetryCharts } from './components/dashboard/TelemetryCharts';
import { TelemetryTable } from './components/dashboard/TelemetryTable';
import { ConveyorsView } from './components/views/ConveyorsView';
import { MultimodalMonitorCard } from './components/dashboard/MultimodalMonitorCard';
import { AlertTriangle, RefreshCw, Radio, ChevronUp, ChevronDown } from 'lucide-react';
import { UnifiedConveyorEvent } from './types/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [isArchitectureOpen, setIsArchitectureOpen] = useState<boolean>(false);

  // Backend Asset States
  const [conveyors, setConveyors] = useState<Conveyor[]>([]);
  const [selectedConveyorId, setSelectedConveyorId] = useState<number | null>(null);
  const [conveyorDetail, setConveyorDetail] = useState<ConveyorDetail | null>(null);

  const [allNodes, setAllNodes] = useState<SensorNode[]>([]);
  const [selectedNodeCode, setSelectedNodeCode] = useState<string | null>(null);

  // Telemetry & Diagnostic Stream
  const [telemetryHistory, setTelemetryHistory] = useState<Telemetry[]>([]);
  const [latestTelemetry, setLatestTelemetry] = useState<Telemetry | null>(null);
  const [multimodalEvent, setMultimodalEvent] = useState<UnifiedConveyorEvent | null>(null);

  // Connectivity & Polling Controls
  const [apiConnected, setApiConnected] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showOverviewChart, setShowOverviewChart] = useState<boolean>(false);

  // 1. Initial Load: Mines, Conveyors, and Sensor Nodes
  const loadInitialData = useCallback(async () => {
    try {
      setIsRefreshing(true);

      // Verify health
      await api.getHealth();
      setApiConnected(true);

      const [conveyorsData, devicesData] = await Promise.all([
        api.getConveyors().catch(() => [] as Conveyor[]),
        api.getDevices().catch(() => [] as SensorNode[]),
      ]);

      setConveyors(conveyorsData);
      setAllNodes(devicesData);

      if (conveyorsData.length > 0 && selectedConveyorId === null) {
        setSelectedConveyorId(conveyorsData[0].id);
      }

      if (devicesData.length > 0 && selectedNodeCode === null) {
        setSelectedNodeCode(devicesData[0].node_code);
      }
    } catch (err: any) {
      console.warn('Initial data loading failed:', err);
      setApiConnected(false);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedConveyorId, selectedNodeCode]);

  useEffect(() => {
    const init = async () => {
      await loadInitialData();
    };
    init();
  }, [loadInitialData]);

  // 2. Fetch Conveyor Details whenever selectedConveyorId changes
  useEffect(() => {
    if (!selectedConveyorId) return;

    api
      .getConveyorDetail(selectedConveyorId)
      .then((detail) => {
        setConveyorDetail(detail);
        if (detail.sensor_nodes && detail.sensor_nodes.length > 0) {
          const belongs = detail.sensor_nodes.some((n) => n.node_code === selectedNodeCode);
          if (!belongs && selectedNodeCode !== 'ALL') {
            setSelectedNodeCode(detail.sensor_nodes[0].node_code);
          }
        }
      })
      .catch((err) => {
        console.warn(`Could not load detail for conveyor ${selectedConveyorId}:`, err);
      });
  }, [selectedConveyorId, selectedNodeCode]);

  // 3. Telemetry & Multimodal Fetch Function
  const fetchTelemetry = useCallback(async () => {
    if (!selectedNodeCode) return;

    try {
      const [telemData, multiData] = await Promise.all([
        api.getTelemetry(selectedNodeCode, 60).catch(() => [] as Telemetry[]),
        api.getMultimodalLatest(selectedNodeCode !== 'ALL' ? selectedNodeCode : undefined)
          .catch(() => api.getMultimodalLatest().catch(() => null)),
      ]);

      setTelemetryHistory(telemData);
      if (telemData.length > 0) {
        setLatestTelemetry(telemData[0]);
      }
      if (multiData) {
        setMultimodalEvent(multiData);
      }
      setApiConnected(true);
    } catch (err: any) {
      console.warn(`Failed to fetch telemetry/multimodal for node ${selectedNodeCode}:`, err);
      setApiConnected(false);
    }
  }, [selectedNodeCode]);

  // Polling Loop: Continuous telemetry stream every 2s
  useEffect(() => {
    fetchTelemetry();

    const timer = setInterval(() => {
      fetchTelemetry();
    }, 2000);

    return () => clearInterval(timer);
  }, [fetchTelemetry]);


  // Manual Refresh Handler
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([loadInitialData(), fetchTelemetry()]);
    setIsRefreshing(false);
  };

  const activeNode =
    allNodes.find((n) => n.node_code === selectedNodeCode) ||
    allNodes.find((n) => n.node_code === latestTelemetry?.node_code) ||
    allNodes[0] ||
    null;
  const currentConveyor =
    conveyors.find((c) => c.id === selectedConveyorId) || conveyorDetail || null;

  return (
    <div className="min-h-screen bg-background font-grotesk text-foreground selection:bg-coral selection:text-cream">
      {/* Problem Statement & Architecture Modal */}
      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />

      {/* Full Width App Container */}
      <div className="w-full px-4 sm:px-8 lg:px-12 pt-5 pb-16 sm:pt-6 sm:pb-20 space-y-6">
        {/* Top Navigation & Controls */}
        <SiteNav
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          onOpenArchitecture={() => setIsArchitectureOpen(true)}
          conveyors={conveyors}
          selectedConveyorId={selectedConveyorId}
          onSelectConveyor={setSelectedConveyorId}
          sensorNodes={conveyorDetail?.sensor_nodes || allNodes}
          selectedNodeId={selectedNodeCode}
          onSelectNode={setSelectedNodeCode}
          activeNode={activeNode}
          onScenarioTriggered={fetchTelemetry}
        />

        {/* Hardware / Backend Offline Banner */}
        {!apiConnected && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-coral p-4 hard-shadow text-cream font-mono text-xs sm:text-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="size-6 shrink-0 stroke-[2.5]" />
              <div>
                <div className="font-black text-sm uppercase tracking-wider">NO ESP32 CONNECTED · BACKEND OFFLINE</div>
                <div className="text-xs text-cream/90 mt-0.5">
                  Microcontroller serial uplink is disconnected. Run <code className="bg-black/30 px-1.5 py-0.5 rounded font-bold">./run_demo.sh</code> and open <code className="bg-black/30 px-1.5 py-0.5 rounded font-bold">http://localhost:5173</code> to stream live data.
                </div>
              </div>
            </div>
            <button
              onClick={handleManualRefresh}
              className="inline-flex items-center justify-center gap-1.5 rounded-full border-2 border-ink bg-cream px-4 py-2 font-mono text-xs font-black uppercase text-ink hard-shadow-xs transition-transform hover:-translate-y-0.5 cursor-pointer self-start sm:self-auto shrink-0"
            >
              <RefreshCw className={`size-3.5 stroke-[2.5] ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Real Hardware vs Simulation Status Indicator */}
        {apiConnected && (
          <div className="flex items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-cream p-3.5 px-5 hard-shadow text-ink font-mono text-xs">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-black uppercase tracking-wider text-ink/70">Hardware Uplink:</span>
              {latestTelemetry?.source === 'REAL_HARDWARE' && !latestTelemetry?.is_simulated ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-lime px-3 py-0.5 font-bold text-ink hard-shadow-xs">
                  <span className="size-2 rounded-full bg-emerald-600 animate-pulse" />
                  REAL ESP32 HARDWARE CONNECTED
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-rose-200 px-3 py-0.5 font-bold text-rose-950 hard-shadow-xs">
                  <span className="size-2 rounded-full bg-rose-600" />
                  NO ESP32 CONNECTED (OFFLINE / SIMULATED)
                </span>
              )}
              <span className="text-ink/60">
                {latestTelemetry?.source === 'REAL_HARDWARE' && !latestTelemetry?.is_simulated
                  ? 'Receiving physical serial packets from microcontroller'
                  : 'No active USB serial telemetry detected on port /dev/ttyUSB*'}
              </span>
            </div>
            <button
              onClick={handleManualRefresh}
              className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-white px-3 py-1 font-mono text-xs font-bold uppercase text-ink hard-shadow-xs hover:-translate-y-0.5 cursor-pointer shrink-0"
            >
              <RefreshCw className={`size-3 stroke-[2.5] ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        )}

        {/* TAB 1: OVERVIEW (Lightweight, spacious, judge-friendly) */}
        {currentTab === 'overview' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            {/* 1. Executive Health Scorecard + Integrated 1-Click Fault Scenario Switcher */}
            <ExecutiveHealthBanner
              conveyor={currentConveyor}
              activeNode={activeNode}
              latestTelemetry={latestTelemetry}
              onScenarioTriggered={fetchTelemetry}
            />

            {/* 2. Physical Conveyor Digital Twin with 4 Key Vital Signs */}
            <ConveyorTwinDiagram
              conveyor={currentConveyor}
              activeNode={activeNode}
              latestTelemetry={latestTelemetry}
            />

            {/* Optional Collapsible Historical Chart for First-Time Users */}
            <div className="flex items-center justify-center pt-6 sm:pt-8 pb-1">
              <button
                onClick={() => setShowOverviewChart(!showOverviewChart)}
                className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-cream hover:bg-lime px-5 sm:px-6 py-2 font-mono text-xs sm:text-sm font-black uppercase tracking-wider text-ink hard-shadow-xs transition-transform hover:-translate-y-0.5 active:translate-y-0.5 cursor-pointer"
              >
                {showOverviewChart ? (
                  <ChevronUp className="size-4 stroke-[3]" />
                ) : (
                  <ChevronDown className="size-4 stroke-[3]" />
                )}
                <span>{showOverviewChart ? 'Hide Historical Stream' : 'Show Historical Charts (50 Pts)'}</span>
              </button>
            </div>

            {showOverviewChart && (
              <div className="animate-in fade-in duration-200">
                <TelemetryCharts telemetryHistory={telemetryHistory} />
              </div>
            )}
          </div>
        )}

        {/* TAB 2: VISION & EVIDENCE (Dedicated Decoupled Camera + Multimodal Evidence Engine) */}
        {currentTab === 'multimodal' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <MultimodalMonitorCard
              latestTelemetry={latestTelemetry}
              multimodalEvent={multimodalEvent}
              onRefreshCamera={fetchTelemetry}
            />
          </div>
        )}

        {/* TAB 3: ALL SENSORS (Full 6-sensor multi-modal fleet + Charts) */}
        {currentTab === 'sensors' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <SensorCards telemetry={latestTelemetry} />
            <TelemetryCharts telemetryHistory={telemetryHistory} />
          </div>
        )}

        {/* TAB 4: RAW LOGS (Telemetry frames table & export) */}
        {currentTab === 'telemetry' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <TelemetryTable
              telemetryList={telemetryHistory}
              sensorCode={selectedNodeCode || 'ALL'}
              nodes={conveyorDetail?.sensor_nodes || allNodes}
              onSelectNode={setSelectedNodeCode}
            />
          </div>
        )}

        {/* TAB 5: FLEET ASSETS (Mine conveyors and physical rigs) */}
        {currentTab === 'conveyors' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <ConveyorsView
              conveyors={conveyors}
              selectedConveyorDetail={conveyorDetail}
              onSelectConveyor={(id) => {
                setSelectedConveyorId(id);
                setCurrentTab('overview');
              }}
            />
          </div>
        )}

        {/* Empty State when no telemetry is found and backend is connected */}
        {apiConnected && telemetryHistory.length === 0 && (
          <div className="rounded-3xl border-3 border-ink bg-cream p-10 text-center font-mono text-ink hard-shadow">
            <Radio className="size-12 text-coral mx-auto mb-3 animate-pulse stroke-[2.5]" />
            <div className="font-grotesk text-xl font-black uppercase tracking-tight text-ink mb-2">
              Awaiting Telemetry Packets for {selectedNodeCode || 'Node'}
            </div>
            <p className="text-sm font-mono text-ink/70 max-w-md mx-auto mb-4 font-medium">
              Click any scenario in the test bar on the Overview tab to inject simulated readings.
            </p>
          </div>
        )}

        {/* Industrial Chic Footer */}
        <footer className="pt-8 border-t-2 border-ink/20 text-center text-xs sm:text-sm font-mono text-ink/50">
          Intelligent Conveyor Health System
        </footer>
      </div>
    </div>
  );
}

export default App;
