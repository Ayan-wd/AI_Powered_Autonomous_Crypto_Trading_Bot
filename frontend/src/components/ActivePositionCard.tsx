import React from 'react';
import type { ActivePosition } from '../services/api';
import { Layers, ShieldCheck, XCircle, RotateCcw } from 'lucide-react';

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
    <div className="bg-[#09090b] border border-zinc-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div
            className={`p-2 rounded-lg border ${
              hasPos
                ? 'bg-white text-black border-white'
                : 'bg-black text-zinc-400 border-zinc-800'
            }`}
          >
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-white">Active Position & Paper Ledger</h3>
              <span
                className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${
                  hasPos
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 animate-pulse'
                    : 'bg-zinc-900 text-zinc-400 border-zinc-800'
                }`}
              >
                {hasPos ? 'POSITION OPEN' : 'NO OPEN POSITION'}
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              {hasPos ? `${position.symbol} • SPOT ORDER` : '100% Cash / Capital Preservation Active'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasPos && (
            <button
              onClick={onClosePosition}
              disabled={closing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-bold rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition disabled:opacity-50 cursor-pointer shadow-sm"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>{closing ? 'Closing...' : 'Close Position'}</span>
            </button>
          )}

          <button
            onClick={onResetPaper}
            disabled={resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-lg bg-black hover:bg-zinc-900 text-zinc-300 hover:text-white border border-zinc-800 transition disabled:opacity-50 cursor-pointer"
            title="Reset capital back to $10,000.00 (Testnet Balance)"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-white' : ''}`} />
            <span>Reset ($10k)</span>
          </button>
        </div>
      </div>

      {hasPos ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 font-mono">
          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Symbol / Side</div>
            <div className="text-sm font-black text-white mt-1">
              {position.symbol} <span className="text-emerald-400 font-bold">{position.side}</span>
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Entry Price</div>
            <div className="text-sm font-bold text-white mt-1">
              ${position.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Current Price</div>
            <div className="text-sm font-bold text-white mt-1">
              ${position.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Unrealized PnL</div>
            <div
              className={`text-sm font-black mt-1 flex items-center gap-0.5 ${
                isProfit ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isProfit ? '+' : ''}${position.unrealized_pnl_usd.toFixed(2)}
              <span className="text-xs font-normal">
                ({isProfit ? '+' : ''}
                {position.unrealized_pnl_pct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Stop Loss</div>
            <div className="text-sm font-bold text-rose-400 mt-1">
              {position.stop_loss ? `$${position.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : 'N/A'}
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
            <div className="text-[10px] text-zinc-400 uppercase">Take Profit</div>
            <div className="text-sm font-bold text-emerald-400 mt-1">
              {position.take_profit ? `$${position.take_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : 'N/A'}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between bg-black/40 border border-zinc-800/60 rounded-lg p-4 font-mono text-xs">
          <div className="flex items-center gap-2 text-zinc-400">
            <ShieldCheck className="w-4 h-4 text-zinc-400" />
            <span>Autonomous Risk Engine: Zero exposure. Capital is fully preserved in cash reserve.</span>
          </div>
          <span className="text-zinc-400">Ready for high-probability confluence</span>
        </div>
      )}
    </div>
  );
};
