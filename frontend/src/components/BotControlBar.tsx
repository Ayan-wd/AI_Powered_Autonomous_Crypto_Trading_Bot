import React from 'react';
import type { BotDaemonStatus } from '../services/api';
import { Play, Square, Cpu, CheckCircle2, Clock } from 'lucide-react';

interface BotControlBarProps {
  botDaemon: BotDaemonStatus | null;
  onStartBot: () => void;
  onStopBot: () => void;
  loading: boolean;
}

export const BotControlBar: React.FC<BotControlBarProps> = ({
  botDaemon,
  onStartBot,
  onStopBot,
  loading,
}) => {
  const isRunning = botDaemon?.is_running ?? false;

  return (
    <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-lg shadow-indigo-950/20">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center border transition-all ${
            isRunning
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-md shadow-emerald-500/20 animate-pulse'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}
        >
          <Cpu className="w-5 h-5" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white tracking-wide">
              Autonomous Execution Daemon
            </h3>
            <span
              className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${
                isRunning
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
            >
              {isRunning ? 'DAEMON ACTIVE' : 'DAEMON IDLE'}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400 font-mono mt-0.5">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-indigo-400" />
              Pair: {botDaemon?.symbol || 'BTCUSDT'} ({botDaemon?.timeframe || '15m'})
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              Ticks Evaluated: {botDaemon?.iteration_count ?? 0}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {isRunning ? (
          <button
            onClick={onStopBot}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 transition-colors disabled:opacity-50 cursor-pointer shadow-md"
          >
            <Square className="w-3.5 h-3.5" />
            <span>Stop Autonomous Bot</span>
          </button>
        ) : (
          <button
            onClick={onStartBot}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-950/50 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Autonomous Paper Bot</span>
          </button>
        )}
      </div>
    </div>
  );
};
