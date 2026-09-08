import React from 'react';
import { Shield, ShieldAlert, Activity, RefreshCw } from 'lucide-react';
import type { BotStatus } from '../types/trading';

interface HeaderProps {
  status: BotStatus | null;
  onRefresh: () => void;
  onKillSwitch: () => void;
  onResetKillSwitch: () => void;
  loading: boolean;
  wsConnected?: boolean;
  isDaemonRunning?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onRefresh,
  onKillSwitch,
  onResetKillSwitch,
  loading,
  wsConnected = false,
  isDaemonRunning = false,
}) => {
  const isEmergency = status?.kill_switch_active;
  const mode = status?.trading_mode || 'PAPER';
  const isRunning = isDaemonRunning || status?.bot_state === 'RUNNING';

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide">QUANTUM AI</h1>
            <p className="text-xs text-slate-400 font-mono">Autonomous Spot Engine v0.1.0</p>
          </div>
        </div>

        {/* Trading Mode Badge */}
        <div className="flex items-center gap-2 pl-4 border-l border-slate-800">
          <span
            className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
              mode === 'LIVE'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse'
                : mode === 'TESTNET'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}
          >
            MODE: {mode}
          </span>

          <span
            className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
              isEmergency
                ? 'bg-rose-500/20 text-rose-300 border-rose-500'
                : isRunning
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-700/50 text-slate-400 border-slate-700'
            }`}
          >
            {isEmergency ? 'EMERGENCY HALT' : isRunning ? 'ACTIVE' : 'STOPPED'}
          </span>

          <span
            className={`px-2 py-0.5 text-[11px] font-mono font-medium rounded-full border flex items-center gap-1 ${
              wsConnected
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-700/60'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
              }`}
            />
            {wsConnected ? 'WS STREAMING' : 'WS CONNECTING'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Sync</span>
        </button>

        {/* Emergency Kill Switch */}
        {isEmergency ? (
          <button
            onClick={onResetKillSwitch}
            className="px-4 py-1.5 text-xs font-semibold text-emerald-300 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-600/50 rounded-lg shadow transition flex items-center gap-1.5"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Reset Kill Switch</span>
          </button>
        ) : (
          <button
            onClick={onKillSwitch}
            className="px-4 py-1.5 text-xs font-semibold text-rose-300 bg-rose-950/80 hover:bg-rose-900 border border-rose-600/50 rounded-lg shadow hover:shadow-rose-900/40 transition flex items-center gap-1.5 group"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 group-hover:scale-110 transition-transform" />
            <span>Kill Switch</span>
          </button>
        )}
      </div>
    </header>
  );
};
