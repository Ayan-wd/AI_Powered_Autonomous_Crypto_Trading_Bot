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
      color: 'border-slate-800 bg-slate-950/40 text-slate-300',
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
      color: 'border-slate-800 bg-slate-950/40 text-indigo-300',
    },
    {
      name: '3. AI Multi-Factor Strategy',
      sub: 'XGBoost ML + Strict Risk Hurdle',
      returnPct: ai?.total_return_pct ?? 0.0,
      netProfit: ai?.net_profit ?? 0.0,
      maxDrawdown: ai?.max_drawdown_pct ?? 0.0,
      trades: ai?.total_trades ?? 0,
      winRate: ai?.win_rate_pct ?? 0.0,
      sharpe: ai?.sharpe_ratio ?? 0.0,
      color: 'border-emerald-500/30 bg-emerald-950/10 text-emerald-300',
      isHighlight: true,
    },
  ];

  return (
    <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">3-Way Quantitative Strategy Benchmark</h3>
            <p className="text-xs text-slate-400">Realistic backtest accounting for 0.10% fees, 0.05% slippage & $50 baseline</p>
          </div>
        </div>

        <button
          onClick={onRunBenchmark}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900 rounded-lg shadow transition flex items-center gap-1.5 cursor-pointer"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Running Simulation...' : 'Run 3-Way Benchmark'}</span>
        </button>
      </div>

      {/* Strategies Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {strategies.map((strat, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-lg border ${strat.color} flex flex-col justify-between transition relative`}
          >
            {strat.isHighlight && (
              <span className="absolute top-2 right-2 text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-1.5 py-0.5 rounded">
                AI ENGINE
              </span>
            )}
            <div>
              <h4 className="text-xs font-bold text-white mb-0.5">{strat.name}</h4>
              <p className="text-[11px] text-slate-400 mb-3">{strat.sub}</p>

              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans text-[11px]">Net Return:</span>
                  <span className={`font-bold ${strat.returnPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {strat.returnPct >= 0 ? '+' : ''}{strat.returnPct.toFixed(2)}% (${strat.netProfit.toFixed(2)})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans text-[11px]">Max Drawdown:</span>
                  <span className="text-rose-300 font-semibold">{strat.maxDrawdown.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans text-[11px]">Total Trades:</span>
                  <span className="text-slate-200">{strat.trades} ({strat.winRate.toFixed(1)}% WR)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans text-[11px]">Sharpe Ratio:</span>
                  <span className="text-cyan-300 font-semibold">{strat.sharpe.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
