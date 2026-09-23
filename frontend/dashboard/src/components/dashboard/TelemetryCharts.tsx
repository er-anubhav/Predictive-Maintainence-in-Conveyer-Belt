import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Telemetry } from '../../types/api';
import { Activity, Thermometer, Gauge, MoveHorizontal, LineChart as ChartIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface TelemetryChartsProps {
  telemetryHistory: Telemetry[];
}

// Neo-Brutalist custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border-2 border-ink bg-cream p-2.5 shadow-md font-mono text-[11px] text-ink hard-shadow-xs select-none">
        <div className="font-bold border-b border-ink/20 pb-1 mb-1">
          UTC: <span>{label}</span>
        </div>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex justify-between items-center gap-4 py-0.5">
            <span style={{ color: entry.color }} className="flex items-center gap-1.5 font-bold">
              <span className="size-2 rounded-full border border-ink" style={{ backgroundColor: entry.color }} />
              {entry.name}:
            </span>
            <span className="font-black font-mono-num text-ink">
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({ telemetryHistory }) => {
  const [activeTab, setActiveTab] = useState<'vibration' | 'temperature' | 'dynamics' | 'tracking'>('vibration');

  const chartData = [...telemetryHistory]
    .reverse()
    .map((item) => {
      const ts = new Date(item.timestamp);
      const timeStr = !isNaN(ts.getTime())
        ? `${ts.getHours().toString().padStart(2, '0')}:${ts.getMinutes().toString().padStart(2, '0')}:${ts.getSeconds().toString().padStart(2, '0')}`
        : '';

      return {
        ...item,
        timeStr,
      };
    });

  return (
    <div className="rounded-2xl border-2 border-ink bg-white p-5 sm:p-7 hard-shadow sm:rounded-[2rem] font-mono space-y-5">
      {/* Header with Title and Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b-2 border-ink/20 pb-4">
        <div className="flex items-center gap-3.5">
          <span className="grid size-12 sm:size-14 shrink-0 place-items-center rounded-2xl bg-lime border-2 border-ink text-xl hard-shadow-xs text-ink">
            <ChartIcon className="size-6 sm:size-7 stroke-[2.5]" />
          </span>
          <div>
            <h3 className="font-grotesk text-xl sm:text-2xl font-bold text-ink uppercase tracking-tight">
              Rolling Telemetry Time Series
            </h3>
            <p className="text-xs sm:text-sm text-ink/75 font-medium mt-0.5">
              High-frequency multi-modal conveyor streams ({telemetryHistory.length} frames plotted)
            </p>
          </div>
        </div>

        {/* Tab Pills */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
          {[
            { id: 'vibration', label: 'Vibration' },
            { id: 'temperature', label: 'Thermal' },
            { id: 'dynamics', label: 'Speed/Load' },
            { id: 'tracking', label: 'Tracking' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={cn(
                'rounded-full border-2 border-ink px-4 sm:px-5 py-1.5 sm:py-2 font-mono text-xs sm:text-sm font-bold uppercase tracking-wider transition-transform cursor-pointer',
                activeTab === t.id
                  ? 'bg-lime text-ink hard-shadow-xs'
                  : 'bg-white text-ink hover:-translate-y-0.5 active:translate-y-0.5'
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Charts View */}
      {chartData.length === 0 ? (
        <div className="h-56 flex items-center justify-center text-sm text-ink/50 uppercase tracking-widest">
          Awaiting telemetry frames to render graphs...
        </div>
      ) : (
        <div className="space-y-6 divide-y-2 divide-ink/10">
          {activeTab === 'vibration' && (
            <div className="pt-2">
              <div className="text-sm sm:text-base font-bold uppercase tracking-wider text-ink mb-3 flex items-center gap-2">
                <Activity className="size-4 sm:size-5 text-[#ffcc4e] stroke-[2.5]" />
                <span>Vibration Dynamics (RMS & Peak in g · Kurtosis)</span>
              </div>
              <div className="h-52 sm:h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#23211E20" vertical={false} />
                    <XAxis dataKey="timeStr" stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <YAxis stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontFamily: 'Georgia', fontSize: '12px', fontWeight: 'bold' }} />
                    <Line type="monotone" dataKey="vibration_rms" name="Vib RMS (g)" stroke="#ffcc4e" strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} />
                    <Line type="monotone" dataKey="vibration_peak" name="Peak (g)" stroke="#FF5D42" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="vibration_kurtosis" name="Kurtosis" stroke="#23211E" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === 'temperature' && (
            <div className="pt-2">
              <div className="text-sm sm:text-base font-bold uppercase tracking-wider text-ink mb-3 flex items-center gap-2">
                <Thermometer className="size-4 sm:size-5 text-coral stroke-[2.5]" />
                <span>Thermal Trend (Bearing Shell °C)</span>
              </div>
              <div className="h-52 sm:h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#23211E20" vertical={false} />
                    <XAxis dataKey="timeStr" stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <YAxis stroke="#23211E" domain={[30, 80]} tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontFamily: 'Georgia', fontSize: '12px', fontWeight: 'bold' }} />
                    <Line type="monotone" dataKey="temperature" name="Temp (°C)" stroke="#FF5D42" strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === 'dynamics' && (
            <div className="pt-2">
              <div className="text-sm sm:text-base font-bold uppercase tracking-wider text-ink mb-3 flex items-center gap-2">
                <Gauge className="size-4 sm:size-5 text-lime stroke-[2.5]" />
                <span>Belt Velocity (m/s) & Load Capacity (%)</span>
              </div>
              <div className="h-52 sm:h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#23211E20" vertical={false} />
                    <XAxis dataKey="timeStr" stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <YAxis stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontFamily: 'Georgia', fontSize: '12px', fontWeight: 'bold' }} />
                    <Line type="monotone" dataKey="belt_speed" name="Speed (m/s)" stroke="#84cc16" strokeWidth={2.5} dot={false} />
                    <Line type="monotone" dataKey="load" name="Load (%)" stroke="#10b981" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === 'tracking' && (
            <div className="pt-2">
              <div className="text-sm sm:text-base font-bold uppercase tracking-wider text-ink mb-3 flex items-center gap-2">
                <MoveHorizontal className="size-4 sm:size-5 text-[#ffcc4e] stroke-[2.5]" />
                <span>Lateral Belt Tracking Deviation (mm)</span>
              </div>
              <div className="h-44 sm:h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#23211E20" vertical={false} />
                    <XAxis dataKey="timeStr" stroke="#23211E" tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <YAxis stroke="#23211E" domain={[-15, 15]} tick={{ fill: '#23211E', fontSize: 11, fontFamily: 'Georgia' }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontFamily: 'Georgia', fontSize: '12px', fontWeight: 'bold' }} />
                    <Line type="monotone" dataKey="tracking_position" name="Offset (mm)" stroke="#ffcc4e" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
