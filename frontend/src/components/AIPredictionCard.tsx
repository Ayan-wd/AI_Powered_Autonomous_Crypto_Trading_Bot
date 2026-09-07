import React from 'react';
import { BrainCircuit, CheckCircle2 } from 'lucide-react';

interface AIPredictionProps {
  symbol?: string;
  probabilities?: {
    buy: number;
    sell: number;
    hold: number;
  };
  decision?: string;
  confidence?: number;
  reasoning?: string[];
}

export const AIPredictionCard: React.FC<AIPredictionProps> = ({
  symbol = 'BTC/USDT',
  probabilities = { buy: 0.18, sell: 0.12, hold: 0.70 },
  decision = 'HOLD / NO TRADE',
  confidence = 0.72,
  reasoning = [
    'RSI (51.4) in neutral zone, no extreme momentum trigger',
    'Price oscillating between EMA20 and EMA50 (Ranging regime)',
    'Expected return (0.18%) is below hurdle rate (0.50% target)',
    'Capital preservation rule: strictly avoiding forced trades in low volatility',
  ],
}) => {
  const buyPct = Math.round(probabilities.buy * 100);
  const sellPct = Math.round(probabilities.sell * 100);
  const holdPct = Math.round(probabilities.hold * 100);

  const isBuy = decision.includes('BUY');
  const isSell = decision.includes('SELL');

  return (
    <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">AI Quantitative Signal Engine</h3>
            <p className="text-xs text-slate-400 font-mono">XGBoost Horizon 4-Candle Estimator</p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs text-slate-400 block">Model Confidence</span>
          <span className="text-sm font-bold text-indigo-300 font-mono">{(confidence * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Decision Pill */}
      <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between mb-4">
        <div>
          <span className="text-xs text-slate-400 block mb-0.5">Statistical Output</span>
          <span className="text-xs font-mono text-slate-300">{symbol} (15m Timeframe)</span>
        </div>
        <div
          className={`px-3 py-1 rounded-md text-xs font-bold tracking-wide flex items-center gap-1.5 ${
            isBuy
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              : isSell
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              : 'bg-slate-800 text-slate-300 border border-slate-700'
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full ${
              isBuy ? 'bg-emerald-400' : isSell ? 'bg-rose-400' : 'bg-slate-400'
            }`}
          />
          {decision}
        </div>
      </div>

      {/* Probability Bar */}
      <div className="space-y-2 mb-5">
        <div className="flex justify-between text-xs text-slate-400 font-medium">
          <span className="text-emerald-400">BUY {buyPct}%</span>
          <span className="text-slate-300 font-semibold">HOLD {holdPct}%</span>
          <span className="text-rose-400">SELL {sellPct}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden flex border border-slate-800">
          <div style={{ width: `${buyPct}%` }} className="bg-emerald-500 transition-all duration-500" />
          <div style={{ width: `${holdPct}%` }} className="bg-slate-500 transition-all duration-500" />
          <div style={{ width: `${sellPct}%` }} className="bg-rose-500 transition-all duration-500" />
        </div>
      </div>

      {/* Numerical Explanations */}
      <div>
        <div className="flex items-center gap-1.5 mb-2.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-300">Deterministic Feature Rationale</span>
        </div>
        <div className="space-y-1.5">
          {reasoning.map((item, idx) => (
            <div
              key={idx}
              className="text-xs text-slate-300 bg-slate-950/40 px-2.5 py-1.5 rounded border border-slate-800/80 flex items-start gap-2"
            >
              <span className="text-indigo-400 font-mono text-[10px] mt-0.5">•</span>
              <span className="leading-relaxed">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
