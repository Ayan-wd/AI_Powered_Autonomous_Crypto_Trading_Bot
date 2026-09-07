import React, { useState } from 'react';
import { History, ArrowUpRight, ArrowDownRight, Clock } from 'lucide-react';
import type { TradeItem } from '../types/trading';

interface TradesTableProps {
  trades: TradeItem[];
}

export const TradesTable: React.FC<TradesTableProps> = ({ trades }) => {
  const [filter, setFilter] = useState<'ALL' | 'PROFIT' | 'LOSS'>('ALL');

  const filteredTrades = trades.filter((t) => {
    if (filter === 'PROFIT') return t.pnl > 0;
    if (filter === 'LOSS') return t.pnl <= 0;
    return true;
  });

  return (
    <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Audited Trade Ledger</h3>
            <p className="text-xs text-slate-400">Complete execution record with deterministic explanations</p>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {(['ALL', 'PROFIT', 'LOSS'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition ${
                filter === f
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filteredTrades.length === 0 ? (
        <div className="py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm font-medium">No recorded trades matching criteria</p>
          <p className="text-xs text-slate-600 mt-1">
            Engine is running in capital preservation mode (holding until high-probability setup occurs)
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Side</th>
                <th className="py-2.5 px-3">Entry</th>
                <th className="py-2.5 px-3">Exit</th>
                <th className="py-2.5 px-3">Qty</th>
                <th className="py-2.5 px-3">P/L (Net)</th>
                <th className="py-2.5 px-3">Fee</th>
                <th className="py-2.5 px-3">AI Prob</th>
                <th className="py-2.5 px-3">Deterministic Reason</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredTrades.map((t) => {
                const isProfitable = t.pnl > 0;
                return (
                  <tr key={t.id || t.trade_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                      {t.entry_time ? new Date(t.entry_time).toLocaleTimeString() : '-'}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-white">{t.symbol}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-bold ${
                          t.side === 'BUY'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {t.side === 'BUY' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {t.side}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200">${t.entry_price.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-slate-200">{t.exit_price ? `$${t.exit_price.toFixed(2)}` : 'OPEN'}</td>
                    <td className="py-2.5 px-3 text-slate-300">{t.quantity.toFixed(4)}</td>
                    <td
                      className={`py-2.5 px-3 font-semibold ${
                        isProfitable ? 'text-emerald-400' : t.pnl < 0 ? 'text-rose-400' : 'text-slate-400'
                      }`}
                    >
                      {t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(3)} ({t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%)
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">${t.fees.toFixed(4)}</td>
                    <td className="py-2.5 px-3 text-indigo-300 font-semibold">
                      {t.model_probability ? `${(t.model_probability * 100).toFixed(0)}%` : '-'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 max-w-xs truncate font-sans" title={t.strategy_reason || ''}>
                      {t.strategy_reason || '-'}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          t.status === 'CLOSED'
                            ? 'bg-slate-800 text-slate-300'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse'
                        }`}
                      >
                        {t.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
