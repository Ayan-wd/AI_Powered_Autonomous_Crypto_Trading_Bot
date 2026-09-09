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
    <div className="p-5 rounded-xl bg-[#09090b] border border-zinc-800 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-black text-white border border-zinc-800">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Audited Trade Ledger</h3>
            <p className="text-xs text-zinc-400 font-mono">Execution record with deterministic explanations</p>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center space-x-1.5 bg-black p-1 rounded-lg border border-zinc-800">
          {(['ALL', 'PROFIT', 'LOSS'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition ${
                filter === f
                  ? 'bg-white text-black shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filteredTrades.length === 0 ? (
        <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-40 text-zinc-400" />
          <p className="text-sm font-medium text-zinc-300">No recorded trades matching criteria</p>
          <p className="text-xs text-zinc-500 mt-1 font-mono">
            Engine is holding capital in cash until high-probability confluence setup occurs
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-black text-zinc-400 font-semibold border-b border-zinc-800">
              <tr>
                <th className="p-3">ID / TIME</th>
                <th className="p-3">SYMBOL</th>
                <th className="p-3">SIDE</th>
                <th className="p-3 text-right">ENTRY</th>
                <th className="p-3 text-right">EXIT</th>
                <th className="p-3 text-right">SIZE ($)</th>
                <th className="p-3 text-right">PNL ($)</th>
                <th className="p-3 text-right">RETURN (%)</th>
                <th className="p-3">STRATEGY REASON</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredTrades.map((t) => {
                const isProfitable = t.pnl > 0;
                const sizeUsd = (t.quantity * t.entry_price).toFixed(2);
                return (
                  <tr key={t.id} className="hover:bg-zinc-900/60 transition duration-150">
                    <td className="p-3 text-zinc-400">
                      <div>#{t.id}</div>
                      <div className="text-[10px] text-zinc-500">
                        {t.entry_time ? t.entry_time.slice(11, 19) : '---'}
                      </div>
                    </td>
                    <td className="p-3 font-bold text-white">{t.symbol}</td>
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          t.side === 'BUY'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {t.side}
                      </span>
                    </td>
                    <td className="p-3 text-right font-medium text-zinc-300">${t.entry_price.toFixed(2)}</td>
                    <td className="p-3 text-right font-medium text-zinc-300">
                      {t.exit_price ? `$${t.exit_price.toFixed(2)}` : '---'}
                    </td>
                    <td className="p-3 text-right text-zinc-400">${sizeUsd}</td>
                    <td
                      className={`p-3 text-right font-bold flex items-center justify-end gap-1 ${
                        isProfitable ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {isProfitable ? (
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      ) : (
                        <ArrowDownRight className="w-3.5 h-3.5" />
                      )}
                      <span>{t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}</span>
                    </td>
                    <td
                      className={`p-3 text-right font-bold ${
                        isProfitable ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
                    </td>
                    <td className="p-3 text-zinc-400 text-[11px] max-w-xs truncate" title={t.strategy_reason || ''}>
                      {t.strategy_reason || 'Automated Strategy Signal'}
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
