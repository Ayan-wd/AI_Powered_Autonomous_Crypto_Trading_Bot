import React from 'react';
import { DollarSign, TrendingUp, Percent, Award, AlertTriangle, ShieldCheck } from 'lucide-react';
import type { AccountSummary, TradeMetrics } from '../types/trading';

interface MetricCardsProps {
  account: AccountSummary | null;
  metrics: TradeMetrics | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ account, metrics }) => {
  const equity = account?.total_equity ?? 50.0;
  const startingCapital = account?.starting_capital ?? 50.0;
  const netProfit = account?.net_profit ?? 0.0;
  const returnPct = account?.return_pct ?? 0.0;
  const drawdown = account?.drawdown_pct ?? 0.0;
  const winRate = metrics?.win_rate_pct ?? 0.0;
  const profitFactor = metrics?.profit_factor ?? 0.0;
  const totalTrades = metrics?.total_trades ?? 0;

  const cards = [
    {
      title: 'Total Account Equity',
      value: `$${equity.toFixed(2)}`,
      subtext: `Starting: $${startingCapital.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10',
      border: 'border-indigo-500/20',
    },
    {
      title: 'Net Profit / Loss',
      value: `${netProfit >= 0 ? '+' : ''}$${netProfit.toFixed(2)}`,
      subtext: `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}% total return`,
      icon: TrendingUp,
      color: netProfit >= 0 ? 'text-emerald-400' : 'text-rose-400',
      bg: netProfit >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10',
      border: netProfit >= 0 ? 'border-emerald-500/20' : 'border-rose-500/20',
    },
    {
      title: 'Win Rate & Trades',
      value: `${winRate.toFixed(1)}%`,
      subtext: `${metrics?.winning_trades || 0}W / ${metrics?.losing_trades || 0}L (${totalTrades} total)`,
      icon: Award,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
    },
    {
      title: 'Profit Factor',
      value: profitFactor >= 999 ? '∞' : profitFactor.toFixed(2),
      subtext: `Gross +$${metrics?.gross_profit.toFixed(2) || '0.00'} / -$${metrics?.gross_loss.toFixed(2) || '0.00'}`,
      icon: Percent,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
    },
    {
      title: 'Max Drawdown',
      value: `${(drawdown * 100).toFixed(2)}%`,
      subtext: `Risk Limit: ${( (account?.max_drawdown_limit_pct ?? 0.10) * 100 ).toFixed(0)}% max`,
      icon: AlertTriangle,
      color: drawdown > 0.05 ? 'text-rose-400' : 'text-emerald-400',
      bg: drawdown > 0.05 ? 'bg-rose-500/10' : 'bg-emerald-500/10',
      border: drawdown > 0.05 ? 'border-rose-500/20' : 'border-emerald-500/20',
    },
    {
      title: 'Risk Allocation',
      value: '1.0% Max Risk',
      subtext: 'Max $10.00 / trade on $50',
      icon: ShieldCheck,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl bg-slate-900/60 border ${card.border} backdrop-blur shadow-sm hover:border-slate-700 transition duration-200`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-400 truncate">{card.title}</span>
              <div className={`p-1.5 rounded-lg ${card.bg}`}>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
            </div>
            <div className="text-xl font-bold text-white tracking-tight">{card.value}</div>
            <div className="text-[11px] font-medium text-slate-400 mt-1 truncate">{card.subtext}</div>
          </div>
        );
      })}
    </div>
  );
};
