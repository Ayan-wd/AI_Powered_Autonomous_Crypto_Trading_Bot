import React from 'react';
import { BrainCircuit, CheckCircle2, RefreshCw } from 'lucide-react';
import type { MLPredictionResponse } from '../services/api';

interface AIPredictionProps {
  symbol?: string;
  prediction?: MLPredictionResponse | null;
  onTrainModel?: () => void;
  training?: boolean;
}

export const AIPredictionCard: React.FC<AIPredictionProps> = ({
  symbol = 'BTC/USDT',
  prediction,
  onTrainModel,
  training = false,
}) => {
  const probabilities = prediction?.probabilities ?? { buy: 0.18, sell: 0.12, hold: 0.70 };
  const decision = prediction?.decision ?? 'HOLD / NO TRADE';
  const confidence = prediction?.confidence ?? 0.72;
  const modelVersion = prediction?.model_version ?? 'XGBoost Quant v1.0';
  const reasoning = prediction?.reasoning ?? [
    'RSI (51.4) in neutral zone, no extreme momentum trigger',
    'Price oscillating between EMA20 and EMA50 (Ranging regime)',
    'Expected return (0.18%) is below hurdle rate (0.50% target)',
    'Capital preservation rule: strictly avoiding forced trades in low volatility',
  ];

  const buyPct = Math.round(probabilities.buy * 100);
  const sellPct = Math.round(probabilities.sell * 100);
  const holdPct = Math.round(probabilities.hold * 100);

  const isBuy = decision.includes('BUY');
  const isSell = decision.includes('SELL');

  return (
    <div className="p-5 rounded-xl bg-[#09090b] border border-zinc-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-black text-white border border-zinc-800">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white">AI Quantitative Signal Engine</h3>
              {onTrainModel && (
                <button
                  onClick={onTrainModel}
                  disabled={training}
                  className="px-2 py-0.5 text-[10px] font-mono text-zinc-300 hover:text-white bg-black hover:bg-zinc-900 border border-zinc-800 rounded flex items-center gap-1 transition cursor-pointer"
                  title="Run Walk-Forward Model Training"
                >
                  <RefreshCw className={`w-2.5 h-2.5 ${training ? 'animate-spin text-white' : ''}`} />
                  <span>{training ? 'Training...' : 'Train ML'}</span>
                </button>
              )}
            </div>
            <p className="text-xs text-zinc-400 font-mono">{modelVersion}</p>
          </div>
        </div>

        <div className="text-right">
          <span
            className={`inline-block px-3 py-1 rounded text-xs font-mono font-bold border ${
              isBuy
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : isSell
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                : 'bg-zinc-900 text-zinc-300 border-zinc-700'
            }`}
          >
            {decision}
          </span>
          <div className="text-[11px] text-zinc-400 font-mono mt-0.5">
            Confidence: <strong className="text-white">{(confidence * 100).toFixed(0)}%</strong>
          </div>
        </div>
      </div>

      {/* Probabilities progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs font-mono mb-1 text-zinc-400">
          <span>
            BUY: <strong className="text-emerald-400">{buyPct}%</strong>
          </span>
          <span>
            HOLD: <strong className="text-zinc-200">{holdPct}%</strong>
          </span>
          <span>
            SELL: <strong className="text-rose-400">{sellPct}%</strong>
          </span>
        </div>
        <div className="w-full h-2 rounded-full overflow-hidden flex bg-zinc-900 border border-zinc-800">
          <div style={{ width: `${buyPct}%` }} className="bg-emerald-500" title={`Buy: ${buyPct}%`} />
          <div style={{ width: `${holdPct}%` }} className="bg-zinc-600" title={`Hold: ${holdPct}%`} />
          <div style={{ width: `${sellPct}%` }} className="bg-rose-500" title={`Sell: ${sellPct}%`} />
        </div>
      </div>

      {/* Model Reasoning */}
      <div className="space-y-1.5 pt-3 border-t border-zinc-800">
        <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider block">
          Inference Drivers ({symbol}):
        </span>
        {reasoning.map((item, idx) => (
          <div key={idx} className="flex items-start space-x-2 text-xs text-zinc-300 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5 text-zinc-500 shrink-0 mt-0.5" />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
