import React, { useState } from 'react';
import { Telemetry, UnifiedConveyorEvent } from '../../types/api';
import { api } from '../../services/api';
import {
  Layers,
  Camera,
  Activity,
  Thermometer,
  Gauge,
  MoveHorizontal,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  Eye,
  RefreshCw,
  FlipHorizontal,
  FlipVertical,
} from 'lucide-react';

interface MultimodalMonitorCardProps {
  latestTelemetry: Telemetry | null;
  multimodalEvent: UnifiedConveyorEvent | null;
  onRefreshCamera?: () => void;
}

export const MultimodalMonitorCard: React.FC<MultimodalMonitorCardProps> = ({
  latestTelemetry,
  multimodalEvent,
  onRefreshCamera,
}) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [streamError, setStreamError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(true);
  const [isMirroredX, setIsMirroredX] = useState(true);
  const [isMirroredY, setIsMirroredY] = useState(false);

  // Overall State
  const overallState =
    multimodalEvent?.overall_state || latestTelemetry?.multimodal_state || 'NORMAL';
  const operatingState =
    multimodalEvent?.operating_state || latestTelemetry?.operating_state || 'LOADED_RUNNING';
  const reasons = multimodalEvent?.reasons ||
    (latestTelemetry?.fusion_reasons ? latestTelemetry.fusion_reasons.split(';') : [
      'Monitored modalities are within their configured POC baseline ranges.',
    ]);

  const cameraFrameRef =
    multimodalEvent?.camera?.value?.camera_frame_ref || latestTelemetry?.camera_frame_ref;
  const isSimulated =
    multimodalEvent?.camera?.is_simulated ?? latestTelemetry?.camera_is_simulated ?? true;
  const cameraStatus = multimodalEvent?.camera?.status || latestTelemetry?.camera_status || 'NORMAL';

  // High-FPS continuous MJPEG live video stream with fallback to snapshot
  const streamUrl = `/api/v1/multimodal/camera/live-stream`;
  const snapshotUrl = cameraFrameRef
    ? `/api/v1/multimodal/camera/evidence/${cameraFrameRef.replace('camera/', '')}`
    : null;
  const activeImageUrl = streamError ? snapshotUrl : streamUrl;

  const getConditionBadge = (state: string) => {
    switch (state) {
      case 'HIGH_SEVERITY':
        return (
          <div className="flex items-center gap-2 rounded-xl border-2 border-rose bg-rose/15 px-4 py-2 text-rose">
            <AlertCircle className="size-6 stroke-[2.5] animate-pulse" />
            <div>
              <div className="font-mono text-xs uppercase font-bold tracking-wider">Overall Condition</div>
              <div className="font-display text-lg font-black tracking-tight">HIGH SEVERITY</div>
            </div>
          </div>
        );
      case 'WARNING':
        return (
          <div className="flex items-center gap-2 rounded-xl border-2 border-amber-500 bg-amber-500/15 px-4 py-2 text-amber-600">
            <AlertTriangle className="size-6 stroke-[2.5]" />
            <div>
              <div className="font-mono text-xs uppercase font-bold tracking-wider">Overall Condition</div>
              <div className="font-display text-lg font-black tracking-tight">WARNING</div>
            </div>
          </div>
        );
      case 'WATCH':
        return (
          <div className="flex items-center gap-2 rounded-xl border-2 border-sky-500 bg-sky-500/15 px-4 py-2 text-sky-600">
            <Activity className="size-6 stroke-[2.5]" />
            <div>
              <div className="font-mono text-xs uppercase font-bold tracking-wider">Overall Condition</div>
              <div className="font-display text-lg font-black tracking-tight">WATCH</div>
            </div>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 rounded-xl border-2 border-emerald-600 bg-emerald-500/15 px-4 py-2 text-emerald-700">
            <CheckCircle2 className="size-6 stroke-[2.5]" />
            <div>
              <div className="font-mono text-xs uppercase font-bold tracking-wider">Overall Condition</div>
              <div className="font-display text-lg font-black tracking-tight">NORMAL</div>
            </div>
          </div>
        );
    }
  };

  const handleCapture = async () => {
    setIsCapturing(true);
    try {
      await api.triggerCameraSnapshot('NORMAL');
      if (onRefreshCamera) {
        await onRefreshCamera();
      }
    } catch (e) {
      console.error('Snapshot failed:', e);
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <div className="rounded-2xl border-2 border-ink bg-cream p-6 sm:p-8 hard-shadow-sm space-y-7">
      {/* 1. Header with Title & Condition Badge */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b-2 border-ink/15 pb-5">
        <div className="flex items-center gap-4">
          <div className="flex size-14 items-center justify-center rounded-2xl border-2 border-ink bg-[#ffcc4e] hard-shadow-xs shrink-0">
            <Layers className="size-8 text-ink stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="font-display font-black text-2xl sm:text-3xl lg:text-4xl text-ink">
                Multimodal Evidence Fusion
              </h2>
              <span className="font-mono text-xs sm:text-sm font-black bg-white border-2 border-ink px-3 py-1 rounded-full text-ink">
                Rule Engine
              </span>
            </div>
          </div>
        </div>

        <div>{getConditionBadge(overallState)}</div>
      </div>

      {/* 2. System Mode & Health Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 font-mono">
        <div className="flex items-center gap-3">
          <span className="text-sm uppercase font-bold text-ink/75">System Mode:</span>
          <span className={`px-4 py-1.5 rounded-lg text-sm sm:text-base font-black uppercase border-2 border-ink ${
            multimodalEvent?.system_mode === 'DEMO_SIMULATED' ? 'bg-amber-400 text-ink' : 'bg-lime text-ink'
          }`}>
            {multimodalEvent?.system_mode === 'DEMO_SIMULATED' ? 'DEMO / SIMULATED' : 'REAL HARDWARE'}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-sm font-bold">
          <span className="text-ink/70 uppercase">Health:</span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.esp32 === 'ONLINE' ? 'bg-emerald-200 text-emerald-950' : 'bg-rose-200 text-rose-950'
          }`}>
            ESP32: {multimodalEvent?.hardware_health?.esp32 === 'ONLINE' ? 'CONNECTED' : 'NOT CONNECTED'}
          </span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.vibration === 'GOOD' ? 'bg-emerald-200 text-emerald-950' : 'bg-amber-200 text-amber-950'
          }`}>
            Vib: {multimodalEvent?.hardware_health?.vibration || 'GOOD'}
          </span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.temperature === 'GOOD' ? 'bg-emerald-200 text-emerald-950' : 'bg-amber-200 text-amber-950'
          }`}>
            Temp: {multimodalEvent?.hardware_health?.temperature || 'GOOD'}
          </span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.rpm === 'GOOD' ? 'bg-emerald-200 text-emerald-950' : 'bg-amber-200 text-amber-950'
          }`}>
            RPM: {multimodalEvent?.hardware_health?.rpm || 'GOOD'}
          </span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.tracking === 'GOOD' ? 'bg-emerald-200 text-emerald-950' : 'bg-amber-200 text-amber-950'
          }`}>
            Track: {multimodalEvent?.hardware_health?.tracking || 'GOOD'}
          </span>
          <span className={`px-3 py-1 rounded-md border-2 border-ink font-mono font-black ${
            multimodalEvent?.hardware_health?.camera === 'ONLINE' ? 'bg-emerald-200 text-emerald-950' : multimodalEvent?.hardware_health?.camera === 'STALE' ? 'bg-amber-200 text-amber-950' : 'bg-rose-200 text-rose-950'
          }`}>
            Cam: {multimodalEvent?.hardware_health?.camera || 'ONLINE'}
          </span>
        </div>
      </div>

      {/* 3. Main Grid: Left side (Large Optical Camera Feed) | Right side (Supporting Evidence + Sensor Readings) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7 items-stretch">
        {/* Left Column (6 cols): Extra-Tall Optical Camera Evidence Feed */}
        <div className="lg:col-span-6 flex flex-col justify-between rounded-2xl border-2 border-ink bg-white overflow-hidden hard-shadow-xs font-mono">
          <div className="flex items-center justify-between px-5 py-4 bg-white border-b-2 border-ink">
            <div className="flex items-center gap-3">
              <Camera className="size-6 text-ink stroke-[2.5]" />
              <span className="text-base sm:text-lg font-black uppercase tracking-wider text-ink">
                Optical Evidence Feed
              </span>
            </div>
            <div className="flex items-center gap-2.5">
              {isSimulated && (
                <span className="rounded-md bg-amber-400 border border-ink px-2.5 py-1 text-xs font-black text-ink uppercase">
                  SIMULATED
                </span>
              )}
              {/* Invert / Mirror Controls */}
              <button
                onClick={async () => {
                  const nextX = !isMirroredX;
                  setIsMirroredX(nextX);
                  try {
                    await api.setCameraFlip(nextX, isMirroredY);
                    if (onRefreshCamera) onRefreshCamera();
                  } catch (e) {
                    console.error('Failed to set camera horizontal flip:', e);
                  }
                }}
                title={isMirroredX ? "Disable Horizontal Mirror" : "Invert Horizontal (Mirror Flip)"}
                className={`rounded-lg border-2 border-ink p-1.5 transition-colors text-ink cursor-pointer ${
                  isMirroredX ? 'bg-lime' : 'hover:bg-cream'
                }`}
              >
                <FlipHorizontal className="size-4 sm:size-5" />
              </button>
              <button
                onClick={async () => {
                  const nextY = !isMirroredY;
                  setIsMirroredY(nextY);
                  try {
                    await api.setCameraFlip(isMirroredX, nextY);
                    if (onRefreshCamera) onRefreshCamera();
                  } catch (e) {
                    console.error('Failed to set camera vertical flip:', e);
                  }
                }}
                title={isMirroredY ? "Disable Vertical Flip" : "Invert Vertical (Upside Down)"}
                className={`rounded-lg border-2 border-ink p-1.5 transition-colors text-ink cursor-pointer ${
                  isMirroredY ? 'bg-lime' : 'hover:bg-cream'
                }`}
              >
                <FlipVertical className="size-4 sm:size-5" />
              </button>

              {onRefreshCamera && (
                <button
                  onClick={handleCapture}
                  disabled={isCapturing}
                  title="Capture New Snapshot"
                  className="rounded-lg border-2 border-ink p-1.5 hover:bg-cream transition-colors text-ink cursor-pointer"
                >
                  <RefreshCw className={`size-4 sm:size-5 ${isCapturing ? 'animate-spin' : ''}`} />
                </button>
              )}
            </div>
          </div>

          <div className="relative min-h-[380px] sm:min-h-[460px] lg:min-h-[480px] bg-neutral-900 flex items-center justify-center overflow-hidden flex-1">
            {activeImageUrl ? (
              <img
                key={activeImageUrl}
                src={activeImageUrl}
                alt="Conveyor Belt Camera Inspection"
                className="w-full h-full object-cover"
                onError={() => {
                  if (!streamError && snapshotUrl) {
                    setStreamError(true);
                  } else {
                    setIsLoaded(false);
                  }
                }}
                onLoad={() => {
                  setIsLoaded(true);
                }}
              />
            ) : null}

            {/* Fallback overlay only when image has not loaded yet */}
            {(!activeImageUrl || !isLoaded) && (
              <div
                className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center pointer-events-none bg-neutral-950/70"
              >
                <Eye className="size-12 text-white/60 mb-3 stroke-[1.5]" />
                <span className="text-base sm:text-lg text-white font-black">
                  Belt Inspection Feed ({cameraStatus})
                </span>
                <span className="text-sm text-white/75 mt-1">
                  ROI Geometry & Surface Tear Extraction Active
                </span>
              </div>
            )}
          </div>

          <div className="p-4 bg-white border-t-2 border-ink flex items-center justify-between text-sm sm:text-base font-bold text-ink">
            <span>Visual Condition: <strong className="text-ink font-black">{cameraStatus}</strong></span>
            <span className="text-emerald-700">● LIVE INSPECTION</span>
          </div>
        </div>

        {/* Right Column (6 cols): Evidence & Live Readings with generous height */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-6">
          {/* Supporting Evidence Area */}
          <div className="space-y-4 font-mono">
            <div className="flex items-center justify-between border-b-2 border-ink/15 pb-2.5">
              <div className="flex items-center gap-2.5 text-base sm:text-lg font-black uppercase tracking-wide text-ink">
                <HelpCircle className="size-5 text-ink stroke-[2.5]" />
                <span>Supporting Evidence & Root Cause</span>
              </div>
              <span className="text-xs sm:text-sm font-black bg-white border-2 border-ink px-3 py-1 rounded-md text-ink">
                {operatingState}
              </span>
            </div>

            <div className="space-y-3 py-2">
              {reasons.map((reason, idx) => (
                <div key={idx} className="flex items-start gap-3 text-lg sm:text-xl font-bold text-ink leading-relaxed">
                  <span className="text-amber-700 text-2xl font-black shrink-0">▶</span>
                  <span>{reason.trim()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 4 Sensor Modalities: Large Tall Neo-Brutalist Cards */}
          <div className="grid grid-cols-2 gap-3.5 sm:gap-4 font-mono pt-2">
            {/* 1. Vibration */}
            <div className="rounded-xl border-2 border-ink bg-amber-50 p-5 space-y-2 hard-shadow-xs">
              <div className="flex items-center justify-between text-sm font-bold text-amber-950 uppercase">
                <span>Vibration</span>
                <Activity className="size-5 text-amber-900" />
              </div>
              <div className="font-black text-2xl sm:text-3xl text-ink">
                {latestTelemetry?.vibration_rms ? `${latestTelemetry.vibration_rms.toFixed(2)} g` : '0.38 g'}
              </div>
              <div className="text-sm font-black text-amber-800">
                {latestTelemetry?.persistence_3of5 ? '3-of-5 Alert' : 'Nominal'}
              </div>
            </div>

            {/* 2. Temperature */}
            <div className="rounded-xl border-2 border-ink bg-sky-50 p-5 space-y-2 hard-shadow-xs">
              <div className="flex items-center justify-between text-sm font-bold text-sky-950 uppercase">
                <span>Thermal</span>
                <Thermometer className="size-5 text-sky-900" />
              </div>
              <div className="font-black text-2xl sm:text-3xl text-ink">
                {latestTelemetry?.temperature ? `${latestTelemetry.temperature.toFixed(1)} °C` : '42.0 °C'}
              </div>
              <div className="text-sm font-black text-sky-800">
                {(latestTelemetry?.temperature ?? 0) > 65 ? 'Elevated' : 'Nominal'}
              </div>
            </div>

            {/* 3. Tracking */}
            <div className="rounded-xl border-2 border-ink bg-emerald-50 p-5 space-y-2 hard-shadow-xs">
              <div className="flex items-center justify-between text-sm font-bold text-emerald-950 uppercase">
                <span>Tracking</span>
                <MoveHorizontal className="size-5 text-emerald-900" />
              </div>
              <div className="font-black text-2xl sm:text-3xl text-ink">
                {latestTelemetry?.tracking_position !== undefined
                  ? `${latestTelemetry.tracking_position > 0 ? '+' : ''}${latestTelemetry.tracking_position.toFixed(1)} mm`
                  : '0.0 mm'}
              </div>
              <div className="text-sm font-black text-emerald-800">
                {Math.abs(latestTelemetry?.tracking_position ?? 0) > 12 ? 'Drift Alert' : 'Centered'}
              </div>
            </div>

            {/* 4. Speed & Load */}
            <div className="rounded-xl border-2 border-ink bg-purple-50 p-5 space-y-2 hard-shadow-xs">
              <div className="flex items-center justify-between text-sm font-bold text-purple-950 uppercase">
                <span>Speed / RPM</span>
                <Gauge className="size-5 text-purple-900" />
              </div>
              <div className="font-black text-2xl sm:text-3xl text-ink truncate">
                {latestTelemetry?.belt_speed ? `${latestTelemetry.belt_speed.toFixed(2)}m/s` : '2.8m/s'}
              </div>
              <div className="text-sm font-black text-purple-800 truncate">
                Load: {latestTelemetry?.load ? `${latestTelemetry.load.toFixed(0)}%` : '75%'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
