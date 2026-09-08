import React from 'react';
import { Shield, ShieldAlert, Activity, RefreshCw, Menu } from 'lucide-react';
import type { BotStatus } from '../types/trading';

interface HeaderProps {
  status: BotStatus | null;
  onRefresh: () => void;
  onKillSwitch: () => void;
  onResetKillSwitch: () => void;
  loading: boolean;
  wsConnected?: boolean;
  isDaemonRunning?: boolean;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onRefresh,
  onKillSwitch,
  onResetKillSwitch,
  loading,
  wsConnected = false,
  isDaemonRunning = false,
  onToggleSidebar,
}) => {
  const isEmergency = status?.kill_switch_active;
  const mode = status?.trading_mode || 'PAPER';
  const isRunning = isDaemonRunning || status?.bot_state === 'RUNNING';

  return (
    <header className="border-b border-zinc-800 bg-black/90 backdrop-blur-md px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-40">
      <div className="flex items-center space-x-3 sm:space-x-4">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-white text-black flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.2)]">
            <Activity className="w-4 h-4 text-black stroke-[2.5]" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-black text-white tracking-wider">QUANTUM AI</h1>
            <p className="text-[11px] text-zinc-400 font-mono">Spot Trading Terminal</p>
          </div>
        </div>

        {/* Badges */}
        <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-zinc-800">
          <span
            className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded border ${
              mode === 'LIVE'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse'
                : mode === 'TESTNET'
                ? 'bg-zinc-800 text-white border-zinc-700'
                : 'bg-zinc-900 text-zinc-300 border-zinc-800'
            }`}
          >
            MODE: {mode}
          </span>

          <span
            className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded border ${
              isEmergency
                ? 'bg-rose-500/20 text-rose-300 border-rose-500'
                : isRunning
                ? 'bg-white text-black border-white'
                : 'bg-zinc-900 text-zinc-500 border-zinc-800'
            }`}
          >
            {isEmergency ? 'EMERGENCY HALT' : isRunning ? 'DAEMON ACTIVE' : 'STOPPED'}
          </span>

          <span
            className={`px-2 py-0.5 text-[11px] font-mono font-medium rounded border flex items-center gap-1.5 ${
              wsConnected
                ? 'bg-zinc-900 text-zinc-200 border-zinc-800'
                : 'bg-zinc-950 text-zinc-500 border-zinc-900'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'
              }`}
            />
            {wsConnected ? 'WS LIVE' : 'WS CONNECTING'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-2.5">
        {/* Refresh / Sync Button */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-mono font-medium text-zinc-300 hover:text-white bg-zinc-900 hover:bg-zinc-800 rounded-lg border border-zinc-800 transition flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-white' : ''}`} />
          <span>Sync</span>
        </button>

        {/* Emergency Kill Switch */}
        {isEmergency ? (
          <button
            onClick={onResetKillSwitch}
            className="px-3.5 py-1.5 text-xs font-mono font-bold text-white bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 rounded-lg shadow transition flex items-center gap-1.5"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Reset Kill Switch</span>
          </button>
        ) : (
          <button
            onClick={onKillSwitch}
            className="px-3.5 py-1.5 text-xs font-mono font-bold text-rose-400 hover:text-white bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition flex items-center gap-1.5 group"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 group-hover:scale-110 transition-transform" />
            <span>Kill Switch</span>
          </button>
        )}
      </div>
    </header>
  );
};
