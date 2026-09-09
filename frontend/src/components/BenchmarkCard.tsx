import React from 'react';
import { Scale, Play } from 'lucide-react';
import type { BenchmarkResponse } from '../services/api';

interface BenchmarkCardProps {
  benchmark?: BenchmarkResponse | null;
  onRunBenchmark: () => void;
  loading?: boolean;
}

export const BenchmarkCard: React.FC<BenchmarkCardProps> = ({
  benchmark,
  onRunBenchmark,
  loading = false,
}) => {
  const bnh = benchmark?.strategies?.buy_and_hold;
  const tech = benchmark?.strategies?.technical_cross;
  const ai = benchmark?.strategies?.ai_multi_factor;

  const strategies = [
    {
      name: '1. Buy & Hold Benchmark',
      sub: 'Passive market exposure',
      returnPct: bnh?.total_return_pct ?? 0.0,
      netProfit: bnh?.net_profit ?? 0.0,
      maxDrawdown: bnh?.max_drawdown_pct ?? 0.0,
      trades: bnh?.total_trades ?? 1,
      winRate: bnh?.win_rate_pct ?? (bnh?.net_profit > 0 ? 100 : 0),
      sharpe: bnh?.sharpe_ratio ?? 0.0,
      color: 'border-zinc-800 bg-black/40 text-zinc-300',
    },
    {
      name: '2. Simple Technical (EMA Cross)',
      sub: 'EMA20 / EMA50 + RSI filter',
      returnPct: tech?.total_return_pct ?? 0.0,
      netProfit: tech?.net_profit ?? 0.0,
      maxDrawdown: tech?.max_drawdown_pct ?? 0.0,
      trades: tech?.total_trades ?? 0,
      winRate: tech?.win_rate_pct ?? 0.0,
      sharpe: tech?.sharpe_ratio ?? 0.0,
      color: 'border-zinc-800 bg-black/40 text-zinc-300',
    },
    {
      name: '3. AI Multi-Factor Strategy',
      sub: 'XGBoost ML + Strict Hurdle',
      returnPct: ai?.total_return_pct ?? 0.0,
      netProfit: ai?.net_profit ?? 0.0,
      maxDrawdown: ai?.max_drawdown_pct ?? 0.0,
      trades: ai?.total_trades ?? 0,
      winRate: ai?.win_rate_pct ?? 0.0,
      sharpe: ai?.sharpe_ratio ?? 0.0,
      color: 'border-white/40 bg-zinc-900/80 text-white',
      isHighlight: true,
    },
  ];

  return (
    <div className="p-5 rounded-xl bg-[#09090b] border border-zinc-800 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-black text-white border border-zinc-800">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">3-Way Strategy Benchmark Comparator</h3>
            <p className="text-xs text-zinc-400 font-mono">Simultaneous walk-forward evaluation on same market candle stream</p>
          </div>
        </div>

        <button
          onClick={onRunBenchmark}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-lg bg-white hover:bg-zinc-200 text-black shadow-sm transition disabled:opacity-50 cursor-pointer"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Running Comparator...' : 'Run Comparative Benchmark'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
        {strategies.map((strat, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${strat.color} transition flex flex-col justify-between`}
          >
            <div>
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-xs font-bold text-white tracking-wide">{strat.name}</h4>
                {strat.isHighlight && (
                  <span className="text-[9px] bg-white text-black font-bold px-1.5 py-0.2 rounded uppercase">
                    Core Model
                  </span>
                )}
              </div>
              <p className="text-[11px] text-zinc-400 mb-3">{strat.sub}</p>

              <div className="space-y-2 text-xs border-t border-zinc-800/80 pt-2.5">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Total Return</span>
                  <span
                    className={`font-bold ${
                      strat.returnPct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {strat.returnPct >= 0 ? '+' : ''}{strat.returnPct.toFixed(2)}% (${strat.netProfit.toFixed(2)})
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Max Drawdown</span>
                  <span className="text-white font-medium">{strat.maxDrawdown.toFixed(2)}%</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Win Rate</span>
                  <span className="text-white font-medium">{strat.winRate.toFixed(1)}%</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Sharpe Ratio</span>
                  <span className="text-white font-medium">{strat.sharpe.toFixed(2)}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Trades Executed</span>
                  <span className="text-white font-medium">{strat.trades}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
