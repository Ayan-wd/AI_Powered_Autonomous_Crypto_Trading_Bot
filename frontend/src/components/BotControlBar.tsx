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
    <div className="bg-[#09090b] border border-zinc-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-xl">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center border transition-all ${
            isRunning
              ? 'bg-white text-black border-white shadow-[0_0_15px_rgba(255,255,255,0.2)]'
              : 'bg-black text-zinc-400 border-zinc-800'
          }`}
        >
          <Cpu className="w-5 h-5" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white tracking-wide">
              Autonomous Execution Engine
            </h3>
            <span
              className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${
                isRunning
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-zinc-900 text-zinc-400 border-zinc-800'
              }`}
            >
              {isRunning ? 'DAEMON ACTIVE' : 'DAEMON IDLE'}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-zinc-400 font-mono mt-0.5">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-zinc-300" />
              Target: {botDaemon?.symbol === 'ALL' ? 'Multi-Coin Scanner' : botDaemon?.symbol || selectedSymbol} ({botDaemon?.timeframe || selectedTimeframe})
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-zinc-500" />
              Ticks: {botDaemon?.iteration_count ?? 0}
            </span>
          </div>
        </div>
      </div>

      {/* Coin & Timeframe Selectors + Action Controls */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Coin Selector */}
        <div className="flex items-center gap-1.5 bg-black border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs">
          <Coins className="w-3.5 h-3.5 text-zinc-300" />
          <select
            value={selectedSymbol}
            onChange={(e) => onSymbolChange(e.target.value)}
            disabled={isRunning || loading}
            className="bg-transparent text-white focus:outline-none cursor-pointer text-xs font-semibold pr-1 font-mono"
          >
            {SUPPORTED_COINS.map((c) => (
              <option key={c.value} value={c.value} className="bg-zinc-900 text-white">
                {c.label}
              </option>
            ))}
          </select>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1.5 bg-black border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs">
          <Clock className="w-3.5 h-3.5 text-zinc-300" />
          <select
            value={selectedTimeframe}
            onChange={(e) => onTimeframeChange(e.target.value)}
            disabled={isRunning || loading}
            className="bg-transparent text-white focus:outline-none cursor-pointer text-xs font-semibold pr-1 font-mono"
          >
            {TIMEFRAMES.map((t) => (
              <option key={t.value} value={t.value} className="bg-zinc-900 text-white">
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {isRunning ? (
          <button
            onClick={onStopBot}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold font-mono rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all disabled:opacity-50 cursor-pointer shadow-sm"
          >
            <Square className="w-3.5 h-3.5" />
            <span>Stop Engine</span>
          </button>
        ) : (
          <button
            onClick={() => onStartBot(selectedSymbol, selectedTimeframe)}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold font-mono rounded-lg bg-white hover:bg-zinc-200 text-black shadow-md hover:shadow-white/10 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Bot ({selectedSymbol === 'ALL' ? 'Multi' : selectedSymbol})</span>
          </button>
        )}
      </div>
    </div>
  );
};
