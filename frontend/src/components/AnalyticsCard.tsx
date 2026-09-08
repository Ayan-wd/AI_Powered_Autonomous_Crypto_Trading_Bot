import React from 'react';
import { BarChart3, TrendingUp, Award, Clock, DollarSign, PieChart, Sparkles } from 'lucide-react';

interface AnalyticsCardProps {
  analytics: any | null;
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({ analytics }) => {
  const tradePerf = analytics?.trade_performance || {};
  const riskMetrics = analytics?.risk_adjusted_metrics || {};

  const winRate = tradePerf.win_rate_pct ?? 0.0;
  const profitFactor = tradePerf.profit_factor ?? 0.0;
  const expectancy = tradePerf.expectancy_usd ?? 0.0;
  const sharpe = riskMetrics.sharpe_ratio ?? 0.0;
  const sortino = riskMetrics.sortino_ratio ?? 0.0;
  const payoffRatio = tradePerf.payoff_ratio ?? 0.0;
  const avgHoldMins = tradePerf.average_holding_time_minutes ?? 0.0;
  const exitBreakdown = tradePerf.exit_reasons_breakdown || {};

  return (
    <div className="bg-[#09090b] border border-zinc-800 rounded-xl p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-black rounded-lg text-white border border-zinc-800">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-white">Institutional Performance Analytics</h3>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded border bg-zinc-900 text-zinc-300 border-zinc-700">
                AUDITED
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              Risk-Adjusted Ratios & Trade Expectancy Analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-zinc-400">
          <span>Closed Trades: <strong className="text-white">{tradePerf.closed_trades_count ?? 0}</strong></span>
        </div>
      </div>

      {/* Primary Analytics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {/* Win Rate */}
        <div className="bg-black/60 border border-zinc-800/90 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-zinc-400 font-mono">
            <span>Win Rate</span>
            <Award className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="text-lg font-black font-mono text-emerald-400 mt-1">
            {winRate.toFixed(1)}%
          </div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">
            {tradePerf.winning_trades ?? 0}W / {tradePerf.losing_trades ?? 0}L
          </div>
        </div>

        {/* Profit Factor */}
        <div className="bg-black/60 border border-zinc-800/90 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-zinc-400 font-mono">
            <span>Profit Factor</span>
            <TrendingUp className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="text-lg font-black font-mono text-white mt-1">
            {profitFactor >= 999 ? '∞' : profitFactor.toFixed(2)}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">
            Gross W: ${tradePerf.gross_profit_usd?.toFixed(2) || '0.00'}
          </div>
        </div>

        {/* Trade Expectancy */}
        <div className="bg-black/60 border border-zinc-800/90 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-zinc-400 font-mono">
            <span>Expectancy</span>
            <DollarSign className="w-3.5 h-3.5 text-white" />
          </div>
          <div
            className={`text-lg font-black font-mono mt-1 ${
              expectancy >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {expectancy >= 0 ? '+' : ''}${expectancy.toFixed(2)}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">Per Trade Expected PnL</div>
        </div>

        {/* Sharpe Ratio */}
        <div className="bg-black/60 border border-zinc-800/90 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-zinc-400 font-mono">
            <span>Sharpe Ratio</span>
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="text-lg font-black font-mono text-white mt-1">
            {sharpe.toFixed(2)}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">Risk-Free Rate: 0%</div>
        </div>
      </div>

      {/* Secondary Metrics & Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 border-t border-zinc-900 font-mono text-xs">
        <div className="flex items-center justify-between bg-black/40 px-3 py-2 rounded-lg border border-zinc-900">
          <span className="text-zinc-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-zinc-500" />
            Avg Holding Time
          </span>
          <span className="text-white font-bold">{avgHoldMins.toFixed(1)} mins</span>
        </div>

        <div className="flex items-center justify-between bg-black/40 px-3 py-2 rounded-lg border border-zinc-900">
          <span className="text-zinc-400">Sortino Ratio</span>
          <span className="text-white font-bold">{sortino.toFixed(2)}</span>
        </div>

        <div className="flex items-center justify-between bg-black/40 px-3 py-2 rounded-lg border border-zinc-900">
          <span className="text-zinc-400">Payoff Ratio (W/L)</span>
          <span className="text-white font-bold">{payoffRatio.toFixed(2)}</span>
        </div>
      </div>

      {/* Exit Reasons Breakdown */}
      {Object.keys(exitBreakdown).length > 0 && (
        <div className="mt-3 pt-3 border-t border-zinc-900">
          <div className="text-[10px] uppercase text-zinc-400 font-mono mb-2 flex items-center gap-1.5">
            <PieChart className="w-3 h-3 text-zinc-400" />
            <span>Execution Exit Triggers</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(exitBreakdown).map(([reason, count]: [string, any]) => (
              <span
                key={reason}
                className="px-2.5 py-1 text-[11px] font-mono rounded-md bg-black border border-zinc-800 text-zinc-300 flex items-center gap-1.5"
              >
                <span className="text-zinc-400">{reason}:</span>
                <strong className="text-white">{count}</strong>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
