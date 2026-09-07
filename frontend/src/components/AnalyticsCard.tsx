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
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-slate-200">Institutional Performance Analytics</h3>
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-full border bg-indigo-500/20 text-indigo-300 border-indigo-500/40">
                AUDITED METRICS
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Risk-Adjusted Ratios & Trade Expectancy Analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-slate-400">
          <span>Closed Trades: <strong className="text-slate-200">{tradePerf.closed_trades_count ?? 0}</strong></span>
        </div>
      </div>

      {/* Primary Analytics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {/* Win Rate */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-slate-400 font-mono">
            <span>Win Rate</span>
            <Award className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
            {winRate.toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {tradePerf.winning_trades ?? 0}W / {tradePerf.losing_trades ?? 0}L
          </div>
        </div>

        {/* Profit Factor */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-slate-400 font-mono">
            <span>Profit Factor</span>
            <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-lg font-bold font-mono text-indigo-300 mt-1">
            {profitFactor > 900 ? '∞' : profitFactor.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Payoff: {payoffRatio.toFixed(2)}:1
          </div>
        </div>

        {/* Trade Expectancy */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-slate-400 font-mono">
            <span>Expectancy</span>
            <DollarSign className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className={`text-lg font-bold font-mono mt-1 ${expectancy >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {expectancy >= 0 ? '+' : ''}${expectancy.toFixed(3)}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Per Trade Edge ({tradePerf.expectancy_pct ?? 0}%)
          </div>
        </div>

        {/* Sharpe / Sortino Ratio */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center justify-between text-[10px] uppercase text-slate-400 font-mono">
            <span>Sharpe Ratio</span>
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg font-bold font-mono text-cyan-300 mt-1">
            {sharpe.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Sortino: {sortino.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Secondary Details: Hold Times & Exit Reasons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 font-mono text-xs">
        {/* Holding Time and Fees */}
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Avg Holding Time:
            </span>
            <span className="font-semibold text-slate-200">
              {avgHoldMins > 0 ? `${avgHoldMins.toFixed(1)} mins` : 'N/A'}
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400">Total Fees Incurred:</span>
            <span className="font-semibold text-rose-400/90">
              ${(tradePerf.total_fees_paid ?? 0).toFixed(4)} USD
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400">Max Win / Loss Streak:</span>
            <span className="font-semibold text-slate-200">
              {tradePerf.max_consecutive_wins ?? 0} Wins / {tradePerf.max_consecutive_losses ?? 0} Losses
            </span>
          </div>
        </div>

        {/* Exit Reasons Distribution */}
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <PieChart className="w-3.5 h-3.5 text-indigo-400" />
            <span>Exit Reason Distribution:</span>
          </div>
          {Object.keys(exitBreakdown).length > 0 ? (
            <div className="space-y-1">
              {Object.entries(exitBreakdown).map(([reason, count]) => (
                <div key={reason} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">{reason}:</span>
                  <span className="text-slate-200 font-bold">{count as number} trades</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-slate-500 italic">
              No closed trades yet to compute distribution.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
