import { useState, useEffect, useCallback } from 'react';
import { api, getApiBase, setApiBase } from './services/api';
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
import { AlertTriangle, RefreshCw, Radio, ChevronUp, ChevronDown, Settings } from 'lucide-react';
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
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showOverviewChart, setShowOverviewChart] = useState<boolean>(false);
  const [showApiSettings, setShowApiSettings] = useState<boolean>(false);
  const [customApiUrl, setCustomApiUrl] = useState<string>(getApiBase());

  // 1. Initial Load: Mines, Conveyors, and Sensor Nodes
  const loadInitialData = useCallback(async () => {
    try {
      setIsRefreshing(true);

      // Verify health
      const health = await api.getHealth();
      const isDemo = health.status === 'demo_mode' || health.environment === 'demo_simulation';
      setIsDemoMode(isDemo);
      setApiConnected(!isDemo);

      const [conveyorsData, devicesData] = await Promise.all([
        api.getConveyors(),
        api.getDevices(),
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
      console.error('Initial data loading failed:', err);
      setIsDemoMode(true);
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

        {/* Cloud Preview / Backend Connectivity Banner */}
        {isDemoMode && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border-2 border-ink bg-amber-400 p-4 hard-shadow text-ink font-mono text-xs sm:text-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="size-5 shrink-0 stroke-[2.5]" />
              <div>
                <span className="font-black uppercase tracking-wider block sm:inline mr-2">Cloud Preview Mode:</span>
                <span>FastAPI backend not detected on current host. Running interactive demo testbench with realistic mining telemetry.</span>
                <span className="block text-[11px] opacity-80 mt-0.5">
                  To connect live physical hardware & local ML inference, run <code className="font-bold bg-white/60 px-1 py-0.5 rounded">./run_demo.sh</code> and open <code className="font-bold bg-white/60 px-1 py-0.5 rounded">http://localhost:5173</code>
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
              <button
                onClick={() => setShowApiSettings(!showApiSettings)}
                className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-cream px-3 py-1 font-mono text-xs font-black uppercase text-ink hard-shadow-xs transition-transform hover:-translate-y-0.5 cursor-pointer"
              >
                <Settings className="size-3.5 stroke-[2.5]" />
                <span>API URL</span>
              </button>
              <button
                onClick={handleManualRefresh}
                className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-cream px-3 py-1 font-mono text-xs font-black uppercase text-ink hard-shadow-xs transition-transform hover:-translate-y-0.5 cursor-pointer"
              >
                <RefreshCw className={`size-3.5 stroke-[2.5] ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>Retry</span>
              </button>
            </div>
          </div>
        )}

        {/* Custom API URL Configuration Modal */}
        {showApiSettings && (
          <div className="rounded-2xl border-2 border-ink bg-cream p-4 hard-shadow space-y-3 font-mono text-xs">
            <div className="font-bold uppercase tracking-wider text-ink flex items-center gap-2">
              <Settings className="size-4 stroke-[2.5]" />
              <span>Custom Backend API Configuration</span>
            </div>
            <p className="text-muted">
              Enter a custom FastAPI backend URL (e.g., ngrok tunnel or public server IP) to connect this cloud dashboard to your live model & hardware:
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={customApiUrl}
                onChange={(e) => setCustomApiUrl(e.target.value)}
                placeholder="https://your-ngrok-or-backend-url.app"
                className="flex-1 rounded-xl border-2 border-ink bg-white px-3 py-2 text-ink font-mono text-xs focus:outline-none"
              />
              <button
                onClick={() => {
                  setApiBase(customApiUrl);
                  setShowApiSettings(false);
                  handleManualRefresh();
                }}
                className="rounded-xl border-2 border-ink bg-lime px-4 py-2 font-bold uppercase text-ink hard-shadow-xs hover:-translate-y-0.5 cursor-pointer"
              >
                Save & Connect
              </button>
              {customApiUrl && (
                <button
                  onClick={() => {
                    setCustomApiUrl('');
                    setApiBase('');
                    setShowApiSettings(false);
                    handleManualRefresh();
                  }}
                  className="rounded-xl border-2 border-ink bg-coral text-cream px-3 py-2 font-bold uppercase hard-shadow-xs hover:-translate-y-0.5 cursor-pointer"
                >
                  Reset
                </button>
              )}
            </div>
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
