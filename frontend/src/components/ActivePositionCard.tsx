import React from 'react';
import type { ActivePosition } from '../services/api';
import { Layers, ArrowUpRight, ShieldCheck, XCircle, RotateCcw } from 'lucide-react';

interface ActivePositionCardProps {
  position: ActivePosition | null;
  onClosePosition: () => void;
  onResetPaper: () => void;
  closing: boolean;
  resetting: boolean;
}

export const ActivePositionCard: React.FC<ActivePositionCardProps> = ({
  position,
  onClosePosition,
  onResetPaper,
  closing,
  resetting,
}) => {
  const hasPos = position !== null;
  const isProfit = (position?.unrealized_pnl_usd ?? 0) >= 0;

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div
            className={`p-2 rounded-lg border ${
              hasPos
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-slate-200">Active Position & Paper Ledger</h3>
              <span
                className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${
                  hasPos
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {hasPos ? 'POSITION OPEN' : 'NO OPEN POSITION'}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              {hasPos ? `${position.symbol} • LONG SPOT` : '100% Cash / Capital Preservation Active'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasPos && (
            <button
              onClick={onClosePosition}
              disabled={closing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 transition-colors disabled:opacity-50 cursor-pointer shadow-lg shadow-rose-950/40"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>{closing ? 'Closing...' : 'Close Position (Market)'}</span>
            </button>
          )}

          <button
            onClick={onResetPaper}
            disabled={resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
            title="Reset Paper Account Wallet to $50.00"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-amber-400' : ''}`} />
            <span>Reset Wallet</span>
          </button>
        </div>
      </div>

      {hasPos ? (
        <div className="space-y-4">
          {/* Main Position Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Entry Price</div>
              <div className="text-base font-bold font-mono text-slate-200 mt-1">
                ${position.entry_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Mark Price</div>
              <div className="text-base font-bold font-mono text-slate-200 mt-1">
                ${position.current_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Position Size</div>
              <div className="text-base font-bold font-mono text-indigo-300 mt-1">
                ${position.position_value_usd.toFixed(2)}{' '}
                <span className="text-xs text-slate-400 font-normal">({position.quantity.toFixed(5)})</span>
              </div>
            </div>

            <div
              className={`border rounded-lg p-3 ${
                isProfit ? 'bg-emerald-950/30 border-emerald-800/50' : 'bg-rose-950/30 border-rose-800/50'
              }`}
            >
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Unrealized PnL</div>
              <div
                className={`text-base font-bold font-mono mt-1 flex items-center gap-1 ${
                  isProfit ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                <ArrowUpRight className={`w-4 h-4 ${isProfit ? '' : 'rotate-90'}`} />
                <span>
                  {isProfit ? '+' : ''}${position.unrealized_pnl_usd.toFixed(2)} ({position.unrealized_pnl_pct.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Intrabar SL / TP Levels */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs font-mono">
            <div className="p-2.5 bg-slate-950/40 rounded-lg border border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                <span className="text-slate-400">Stop Loss (1 ATR):</span>
              </div>
              <span className="text-rose-400 font-bold">
                ${position.stop_loss ? position.stop_loss.toFixed(2) : 'None'}
              </span>
            </div>

            <div className="p-2.5 bg-slate-950/40 rounded-lg border border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-slate-400">Take Profit (2 ATR):</span>
              </div>
              <span className="text-emerald-400 font-bold">
                ${position.take_profit ? position.take_profit.toFixed(2) : 'None'}
              </span>
            </div>
          </div>

          {/* Strategy Reasoning */}
          {position.strategy_reason && (
            <div className="text-xs text-slate-400 font-mono bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-slate-500 uppercase text-[10px] block mb-0.5">Entry Rationale:</span>
              <p className="text-slate-300">{position.strategy_reason}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="py-6 text-center text-xs text-slate-400 font-mono bg-slate-950/30 rounded-lg border border-slate-800/50 flex flex-col items-center justify-center gap-1.5">
          <ShieldCheck className="w-6 h-6 text-emerald-400/60 mb-1" />
          <p className="text-slate-300 font-medium">All capital parked in cash ($50.00 USD baseline).</p>
          <p className="text-[11px] text-slate-500">
            Autonomous bot is scanning live market ticks and will only enter when statistical edge exceeds fee hurdle.
          </p>
        </div>
      )}
    </div>
  );
};
