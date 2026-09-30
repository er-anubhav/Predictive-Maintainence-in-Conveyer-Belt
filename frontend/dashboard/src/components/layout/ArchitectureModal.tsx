import React from 'react';
import { X, Cpu, Server, Database, HardHat, CheckCircle2 } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ArchitectureModal: React.FC<ArchitectureModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-ink/70 backdrop-blur-xs font-mono select-none animate-in fade-in duration-200">
      <div className="w-full max-w-5xl xl:max-w-6xl rounded-2xl sm:rounded-3xl border-3 sm:border-4 border-ink bg-white p-5 sm:p-7 hard-shadow text-ink">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 mb-4 sm:mb-5 border-b-2 border-ink/15">
          <div className="flex items-center gap-3.5">
            <div className="grid size-13 place-items-center rounded-2xl border-2 border-ink bg-coral hard-shadow-xs text-cream shrink-0">
              <HardHat className="size-7 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h3 className="font-grotesk text-2xl sm:text-3xl font-black uppercase tracking-tight text-ink">
                  System Architecture & Overview
                </h3>
                <span className="rounded-full border-2 border-ink bg-lime px-3 py-1 text-xs sm:text-sm font-black uppercase text-ink">
                  Architecture Guide
                </span>
              </div>
              <p className="text-sm sm:text-base font-semibold text-ink/75 mt-1">
                Intelligent Conveyor Belt Health & Predictive Maintenance in Iron Ore Mining
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="grid size-11 place-items-center rounded-full border-2 border-ink bg-sand/60 hover:bg-coral hover:text-cream text-ink transition-colors cursor-pointer shrink-0"
            title="Close Modal"
          >
            <X className="size-6 stroke-[3]" />
          </button>
        </div>  

        {/* Top Horizontal Row: Challenge (Left) & Mining Conditions (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5">
          {/* 1. Problem Statement Section */}
          <div className="lg:col-span-5 rounded-2xl border-2 border-ink bg-sand/30 p-4 sm:p-5 flex flex-col justify-between">
            <div>
              <h4 className="font-grotesk text-lg sm:text-xl font-black uppercase text-ink flex items-center gap-2.5 mb-2">
                <span className="grid size-7 place-items-center rounded-full bg-coral text-cream text-sm font-black shrink-0">1</span>
                The Mining Challenge
              </h4>
              <p className="text-sm sm:text-base text-ink leading-relaxed font-medium">
                Overland belt conveyors in iron ore mines (e.g. Bailadila and NMDC complexes) carry thousands of tonnes of abrasive ore hourly. Unscheduled stoppages from <strong>roller bearing seizure, belt drift tearing, or splice slap</strong> cost mines <strong>₹25 Lakhs to ₹50 Lakhs per hour</strong> in lost production and emergency repairs.
              </p>
            </div>
          </div>

          {/* 2. Key Innovations for Mining Conditions */}
          <div className="lg:col-span-7 rounded-2xl border-2 border-ink bg-lime/25 p-4 sm:p-5">
            <h4 className="font-grotesk text-lg sm:text-xl font-black uppercase text-ink flex items-center gap-2.5 mb-3">
              <span className="grid size-7 place-items-center rounded-full bg-lime text-ink border-2 border-ink text-sm font-black shrink-0">2</span>
              Engineered for Realistic Mining Conditions
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm sm:text-base">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="size-5 text-emerald-800 shrink-0 mt-0.5" />
                <span className="leading-snug"><strong>Zero-Phase Filtering:</strong> Forward-backward SOS Butterworth removes signal distortion.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="size-5 text-emerald-800 shrink-0 mt-0.5" />
                <span className="leading-snug"><strong>Offline Resilience:</strong> Local SQLite buffers thousands of frames with zero data loss.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="size-5 text-emerald-800 shrink-0 mt-0.5" />
                <span className="leading-snug"><strong>Non-Gaussian Kurtosis:</strong> Kurtosis &gt; 6.0 detects bearing cracks before heat hazards.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="size-5 text-emerald-800 shrink-0 mt-0.5" />
                <span className="leading-snug"><strong>Physical ISO Standards:</strong> Grounded in deterministic physical thresholds without ML hallucinations.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Horizontal Row: 3-Tier Edge Architecture across 3 Columns */}
        <div className="mt-4 sm:mt-5 rounded-2xl border-2 border-ink bg-white p-4 sm:p-5">
          <h4 className="font-grotesk text-lg sm:text-xl font-black uppercase text-ink flex items-center gap-2.5 mb-3.5">
            <span className="grid size-7 place-items-center rounded-full bg-sky text-cream text-sm font-black shrink-0">3</span>
            3-Tier Resilient Edge-to-Cloud Architecture
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Tier 1: ESP32 Edge Node */}
            <div className="rounded-xl border-2 border-ink bg-sky/20 p-3.5 sm:p-4 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-ink text-base sm:text-lg">
                <Cpu className="size-5 text-sky shrink-0" />
                <span>Tier 1: ESP32 Edge Node</span>
              </div>
              <p className="text-sm sm:text-base text-ink leading-snug font-medium">
                Low-cost distributed nodes on idler frames. Samples tri-axial vibration (1000 Hz), thermal PT100, acoustic emission, speed, and laser tracking.
              </p>
            </div>

            {/* Tier 2: Edge Gateway */}
            <div className="rounded-xl border-2 border-ink bg-mint/30 p-3.5 sm:p-4 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-ink text-base sm:text-lg">
                <Server className="size-5 text-emerald-700 shrink-0" />
                <span>Tier 2: Edge Gateway (:9000)</span>
              </div>
              <p className="text-sm sm:text-base text-ink leading-snug font-medium">
                Local SQLite persistent buffer queue. Provides <strong>durable offline buffering</strong> during network dropouts with automated exponential retry.
              </p>
            </div>

            {/* Tier 3: Central DSP & Backend */}
            <div className="rounded-xl border-2 border-ink bg-amber/20 p-3.5 sm:p-4 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-ink text-base sm:text-lg">
                <Database className="size-5 text-amber-800 shrink-0" />
                <span>Tier 3: Central Analytics</span>
              </div>
              <p className="text-sm sm:text-base text-ink leading-snug font-medium">
                FastAPI + PostgreSQL. Runs 4th-order zero-phase Butterworth filtering, Real FFT spectral energy, dominant frequency (f₀), and Kurtosis shock detection.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
