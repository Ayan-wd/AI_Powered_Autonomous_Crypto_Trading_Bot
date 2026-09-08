import React from 'react';
import type { BotDaemonStatus } from '../services/api';
import { Play, Square, Cpu, CheckCircle2, Clock, Coins } from 'lucide-react';

export const SUPPORTED_COINS = [
  { value: 'BTCUSDT', label: 'BTC/USDT (Bitcoin)' },
  { value: 'ETHUSDT', label: 'ETH/USDT (Ethereum)' },
  { value: 'SOLUSDT', label: 'SOL/USDT (Solana)' },
  { value: 'BNBUSDT', label: 'BNB/USDT (Binance Coin)' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT (Dogecoin)' },
  { value: 'ADAUSDT', label: 'ADA/USDT (Cardano)' },
  { value: 'ALL', label: '🔥 Multi-Coin Scanner (Top 6)' },
];

export const TIMEFRAMES = [
  { value: '1m', label: '1m (Ultra-Fast)' },
  { value: '5m', label: '5m (Fast Intraday)' },
  { value: '15m', label: '15m (Standard)' },
  { value: '1h', label: '1h (Swing)' },
];

interface BotControlBarProps {
  botDaemon: BotDaemonStatus | null;
  onStartBot: (sym?: string, tf?: string) => void;
  onStopBot: () => void;
  loading: boolean;
  selectedSymbol: string;
  onSymbolChange: (sym: string) => void;
  selectedTimeframe: string;
  onTimeframeChange: (tf: string) => void;
}

export const BotControlBar: React.FC<BotControlBarProps> = ({
  botDaemon,
  onStartBot,
  onStopBot,
  loading,
  selectedSymbol,
  onSymbolChange,
  selectedTimeframe,
  onTimeframeChange,
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
              Active: {botDaemon?.symbol === 'ALL' ? 'Multi-Coin Scanner' : botDaemon?.symbol || selectedSymbol} ({botDaemon?.timeframe || selectedTimeframe})
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              Ticks: {botDaemon?.iteration_count ?? 0}
            </span>
          </div>
        </div>
      </div>

      {/* Coin & Timeframe Selectors + Action Controls */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Coin Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
          <Coins className="w-3.5 h-3.5 text-amber-400" />
          <select
            value={selectedSymbol}
            onChange={(e) => onSymbolChange(e.target.value)}
            disabled={isRunning || loading}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs font-semibold pr-1"
          >
            {SUPPORTED_COINS.map((c) => (
              <option key={c.value} value={c.value} className="bg-slate-900 text-slate-200">
                {c.label}
              </option>
            ))}
          </select>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <select
            value={selectedTimeframe}
            onChange={(e) => onTimeframeChange(e.target.value)}
            disabled={isRunning || loading}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs font-semibold pr-1"
          >
            {TIMEFRAMES.map((t) => (
              <option key={t.value} value={t.value} className="bg-slate-900 text-slate-200">
                {t.label}
              </option>
            ))}
          </select>
        </div>

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
            onClick={() => onStartBot(selectedSymbol, selectedTimeframe)}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-950/50 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Bot ({selectedSymbol === 'ALL' ? 'Multi' : selectedSymbol})</span>
          </button>
        )}
      </div>
    </div>
  );
};

