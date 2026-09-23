import React, { useState } from 'react';
import { Telemetry } from '../../types/api';
import { ListFilter, Download } from 'lucide-react';

interface TelemetryTableProps {
  telemetryList: Telemetry[];
  sensorCode: string;
  nodes?: Array<{ id?: number; node_code: string; location?: string }>;
  onSelectNode?: (nodeCode: string) => void;
}

export const TelemetryTable: React.FC<TelemetryTableProps> = ({
  telemetryList,
  sensorCode,
  nodes,
  onSelectNode,
}) => {
  const [displayCount, setDisplayCount] = useState<number>(10);

  const displayedRecords = telemetryList.slice(0, displayCount);

  const exportToJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(telemetryList, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `telemetry_${sensorCode}_${new Date().toISOString()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="rounded-2xl border-2 border-ink bg-white p-4 sm:p-6 hard-shadow sm:rounded-[2rem] font-mono text-ink">
      {/* Table Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b-2 border-ink">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="grid size-9 place-items-center rounded-xl border-2 border-ink bg-amber hard-shadow-xs text-ink">
            <ListFilter className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="font-grotesk text-xl sm:text-2xl font-black uppercase tracking-tight text-ink">
              Recent Telemetry Frames Log
            </h3>
            <div className="flex items-center gap-2 text-xs sm:text-sm font-mono text-ink/70">
              <span>Node: <strong className="text-ink">{sensorCode === 'ALL' ? 'All Nodes' : sensorCode}</strong></span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {nodes && nodes.length > 0 && onSelectNode && (
            <div className="flex items-center gap-1.5 text-sm sm:text-base font-mono font-bold">
              <span className="text-ink/70 uppercase">Node:</span>
              <select
                value={sensorCode}
                onChange={(e) => onSelectNode(e.target.value)}
                className="rounded-full border-2 border-ink bg-white px-3.5 py-1 text-sm font-mono font-bold text-ink focus:outline-none cursor-pointer hover:border-coral transition-colors"
              >
                <option value="ALL">All Nodes</option>
                {nodes.map((n) => (
                  <option key={n.id || n.node_code} value={n.node_code}>
                    {n.node_code}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-1.5 text-sm sm:text-base font-mono font-bold">
            <span className="text-ink/70 uppercase">Rows:</span>
            <select
              value={displayCount}
              onChange={(e) => setDisplayCount(Number(e.target.value))}
              className="rounded-full border-2 border-ink bg-white px-3.5 py-1 text-sm font-mono font-bold text-ink focus:outline-none cursor-pointer"
            >
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={30}>30</option>
              <option value={50}>50</option>
            </select>
          </div>

          <button
            onClick={exportToJson}
            disabled={telemetryList.length === 0}
            className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-mint px-4 py-2 font-mono text-xs sm:text-sm font-black uppercase text-ink hard-shadow-xs transition-transform hover:-translate-y-0.5 active:translate-y-0.5 disabled:opacity-50 cursor-pointer"
          >
            <Download className="w-4 h-4 stroke-[2.5]" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Table Scroller */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs sm:text-sm font-mono bg-white">
          <thead className="border-b-2 border-ink bg-white text-xs sm:text-sm font-black uppercase tracking-wider text-ink">
            <tr>
              <th className="py-2.5 px-3">FRAME</th>
              <th className="py-2.5 px-3">TIMESTAMP (UTC)</th>
              <th className="py-2.5 px-3">NODE</th>
              <th className="py-2.5 px-3 text-right">VIB RMS (g)</th>
              <th className="py-2.5 px-3 text-right">PEAK (g)</th>
              <th className="py-2.5 px-3 text-right">KURT</th>
              <th className="py-2.5 px-3 text-right">CREST</th>
              <th className="py-2.5 px-3 text-right">f₀ (Hz)</th>
              <th className="py-2.5 px-3 text-right">AE RMS (V)</th>
              <th className="py-2.5 px-3 text-right">TEMP (°C)</th>
              <th className="py-2.5 px-3 text-right">SPEED (m/s)</th>
              <th className="py-2.5 px-3 text-right">LOAD (%)</th>
              <th className="py-2.5 px-3 text-right">TRACK (mm)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/5 font-mono text-xs sm:text-sm bg-white">
            {displayedRecords.length === 0 ? (
              <tr>
                <td colSpan={13} className="py-12 text-center text-ink/40 font-bold uppercase tracking-wider bg-white">
                  No telemetry records received for this sensor node yet.
                </td>
              </tr>
            ) : (
              displayedRecords.map((rec) => {
                const timeStr = new Date(rec.timestamp).toISOString().replace('T', ' ').replace('Z', '').slice(11, 23);
                const isVibAlert = rec.vibration_rms > 1.2;
                const isTempAlert = rec.temperature > 65;
                const isTrackAlert = Math.abs(rec.tracking_position) > 10;
                const cf = rec.crest_factor !== null && rec.crest_factor !== undefined ? rec.crest_factor.toFixed(2) : '--';
                const f0 = rec.dominant_frequency_hz !== null && rec.dominant_frequency_hz !== undefined ? rec.dominant_frequency_hz.toFixed(1) : '--';

                return (
                  <tr
                    key={rec.id}
                    className="bg-white hover:bg-neutral-50/50 transition-colors text-ink"
                  >
                    <td className="py-2 px-3 font-bold text-ink/30">#{rec.id}</td>
                    <td className="py-2 px-3 font-medium whitespace-nowrap">{timeStr}</td>
                    <td className="py-2 px-3 font-bold text-ink">
                      {onSelectNode ? (
                        <button
                          type="button"
                          onClick={() => onSelectNode(rec.node_code || sensorCode)}
                          className="cursor-pointer hover:text-coral hover:underline transition-colors font-bold"
                          title={`Filter logs for ${rec.node_code || sensorCode}`}
                        >
                          {rec.node_code || sensorCode}
                        </button>
                      ) : (
                        rec.node_code || sensorCode
                      )}
                    </td>
                    <td
                      className={`py-2 px-3 text-right font-bold ${
                        isVibAlert ? 'text-coral font-black underline decoration-2' : rec.vibration_rms > 0.6 ? 'text-amber-800' : 'text-ink'
                      }`}
                    >
                      {rec.vibration_rms.toFixed(3)}
                    </td>
                    <td className="py-2 px-3 text-right text-ink/80">{rec.vibration_peak.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-ink/80">{rec.vibration_kurtosis.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right font-bold text-sky-800">{cf}</td>
                    <td className="py-2 px-3 text-right font-bold text-purple-800">{f0}</td>
                    <td className="py-2 px-3 text-right text-ink/80">{rec.acoustic_rms.toFixed(3)}</td>
                    <td
                      className={`py-2 px-3 text-right font-bold ${
                        isTempAlert ? 'text-coral font-black' : rec.temperature > 50 ? 'text-amber-800' : 'text-ink'
                      }`}
                    >
                      {rec.temperature.toFixed(1)}
                    </td>
                    <td className="py-2 px-3 text-right font-bold text-emerald-800">{rec.belt_speed.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-ink/80">{rec.load.toFixed(1)}</td>
                    <td
                      className={`py-2 px-3 text-right font-bold ${
                        isTrackAlert ? 'text-coral font-black' : 'text-ink'
                      }`}
                    >
                      {rec.tracking_position > 0 ? `+${rec.tracking_position.toFixed(1)}` : rec.tracking_position.toFixed(1)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
