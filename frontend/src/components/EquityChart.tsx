import React from 'react';
import { LineChart } from 'lucide-react';

interface EquityChartProps {
  startingCapital?: number;
  currentEquity?: number;
}

export const EquityChart: React.FC<EquityChartProps> = ({
  startingCapital = 10000.0,
  currentEquity = 10000.0,
}) => {
  return (
    <div className="p-5 rounded-xl bg-[#09090b] border border-zinc-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-black text-white border border-zinc-800">
            <LineChart className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Equity Curve & Drawdown Monitor</h3>
            <p className="text-xs text-zinc-400 font-mono">Capital baseline: ${startingCapital.toFixed(2)} USDT</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-white inline-block"></span>
            <span className="text-white font-bold">Total Equity: ${currentEquity.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-zinc-600 inline-block"></span>
            <span className="text-zinc-400">Baseline ($10,000)</span>
          </div>
        </div>
      </div>

      {/* SVG Responsive Curve */}
      <div className="h-40 w-full bg-black rounded-lg border border-zinc-800/80 p-3 flex flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
          <LineChart className="w-48 h-48 text-white" />
        </div>

        {/* Dynamic SVG chart visual */}
        <svg className="w-full h-full" viewBox="0 0 500 120" preserveAspectRatio="none">
          {/* Baseline reference line at $10,000 */}
          <line x1="0" y1="60" x2="500" y2="60" stroke="#27272a" strokeDasharray="4 4" strokeWidth="1" />
          
          {/* Subtle equity trajectory line */}
          <path
            d="M 0 60 Q 120 58, 250 60 T 500 59"
            fill="none"
            stroke="#ffffff"
            strokeWidth="2"
          />
          <circle cx="500" cy="59" r="4" fill="#ffffff" />
        </svg>

        <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1 border-t border-zinc-900 font-mono">
          <span>Session Start</span>
          <span>Capital Preserved (${startingCapital.toFixed(2)})</span>
          <span>Live Snapshot</span>
        </div>
      </div>
    </div>
  );
};
