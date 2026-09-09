import React from 'react';
import { DollarSign, TrendingUp, Percent, Award, AlertTriangle, ShieldCheck } from 'lucide-react';
import type { AccountSummary, TradeMetrics } from '../types/trading';

interface MetricCardsProps {
  account: AccountSummary | null;
  metrics: TradeMetrics | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ account, metrics }) => {
  const equity = account?.total_equity ?? 10000.0;
  const startingCapital = account?.starting_capital ?? 10000.0;
  const netProfit = account?.net_profit ?? 0.0;
  const returnPct = account?.return_pct ?? 0.0;
  const drawdown = account?.drawdown_pct ?? 0.0;
  const winRate = metrics?.win_rate_pct ?? 0.0;
  const profitFactor = metrics?.profit_factor ?? 0.0;
  const totalTrades = metrics?.total_trades ?? 0;

  const cards = [
    {
      title: 'Total Equity',
      value: `$${equity.toFixed(2)}`,
      subtext: `Starting: $${startingCapital.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-white',
      badge: 'USDT',
    },
    {
      title: 'Net Profit / Loss',
      value: `${netProfit >= 0 ? '+' : ''}$${netProfit.toFixed(2)}`,
      subtext: `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}% total return`,
      icon: TrendingUp,
      color: netProfit >= 0 ? 'text-emerald-400' : 'text-rose-400',
      badge: returnPct >= 0 ? '+RETURN' : '-DRAWDOWN',
    },
    {
      title: 'Win Rate & Count',
      value: `${winRate.toFixed(1)}%`,
      subtext: `${metrics?.winning_trades || 0}W / ${metrics?.losing_trades || 0}L (${totalTrades} total)`,
      icon: Award,
      color: 'text-white',
      badge: `${totalTrades} TRADES`,
    },
    {
      title: 'Profit Factor',
      value: profitFactor >= 999 ? '∞' : profitFactor.toFixed(2),
      subtext: `+$${metrics?.gross_profit.toFixed(2) || '0.00'} / -$${metrics?.gross_loss.toFixed(2) || '0.00'}`,
      icon: Percent,
      color: 'text-white',
      badge: 'RATIO',
    },
    {
      title: 'Max Drawdown',
      value: `${(drawdown * 100).toFixed(2)}%`,
      subtext: `Risk Limit: ${( (account?.max_drawdown_limit_pct ?? 0.95) * 100 ).toFixed(0)}% max`,
      icon: AlertTriangle,
      color: drawdown > 0.15 ? 'text-rose-400' : 'text-emerald-400',
      badge: 'GUARD',
    },
    {
      title: 'Risk Allocation',
      value: '25% Max Risk',
      subtext: 'Max $10,000 / trade on Testnet',
      icon: ShieldCheck,
      color: 'text-zinc-300',
      badge: 'MAX RISK',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="p-4 rounded-xl bg-[#09090b] border border-zinc-800 hover:border-zinc-700 transition duration-200 shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-medium text-zinc-400 truncate">{card.title}</span>
              <div className="p-1.5 rounded-lg bg-black border border-zinc-800">
                <Icon className={`w-3.5 h-3.5 ${card.color}`} />
              </div>
            </div>
            <div>
              <div className={`text-xl font-black font-mono tracking-tight ${card.color}`}>{card.value}</div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-zinc-900 text-[11px] font-mono text-zinc-400">
                <span className="truncate">{card.subtext}</span>
                <span className="text-[9px] bg-zinc-900 text-zinc-400 px-1 py-0.2 rounded border border-zinc-800 shrink-0 ml-1">
                  {card.badge}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
