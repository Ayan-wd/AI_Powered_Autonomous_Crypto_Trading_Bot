import React from 'react';
import { LineChart } from 'lucide-react';

interface EquityChartProps {
  startingCapital?: number;
  currentEquity?: number;
}

export const EquityChart: React.FC<EquityChartProps> = ({
  startingCapital = 50.0,
  currentEquity = 50.0,
}) => {
  return (
    <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
            <LineChart className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Equity Curve & Drawdown Monitor</h3>
            <p className="text-xs text-slate-400">Capital baseline: ${startingCapital.toFixed(2)} USD</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
            <span className="text-slate-300">Total Equity: ${currentEquity.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500/50 inline-block"></span>
            <span className="text-slate-400">Baseline ($50)</span>
          </div>
        </div>
      </div>

      {/* SVG Responsive Mock Curve */}
      <div className="h-44 w-full bg-slate-950/60 rounded-lg border border-slate-800/80 p-3 flex flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center opacity-10 pointer-events-none">
          <LineChart className="w-48 h-48 text-indigo-400" />
        </div>

        {/* Dynamic SVG chart visual */}
        <svg className="w-full h-full" viewBox="0 0 500 120" preserveAspectRatio="none">
          {/* Baseline reference line at $50 */}
          <line x1="0" y1="60" x2="500" y2="60" stroke="#334155" strokeDasharray="4 4" strokeWidth="1" />
          
          {/* Subtle equity trajectory line */}
          <path
            d="M 0 60 Q 120 58, 250 60 T 500 59"
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
          />
          <circle cx="500" cy="59" r="4" fill="#34d399" />
        </svg>

        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/60 font-mono">
          <span>Session Start</span>
          <span>Capital Preserved ($50.00)</span>
          <span>Live Snapshot</span>
        </div>
      </div>
    </div>
  );
};
