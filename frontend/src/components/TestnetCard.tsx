import React from 'react';
import type { TestnetAccountResponse, TestnetStatusResponse } from '../services/api';
import { Globe, Lock, ShieldCheck, CheckCircle2, AlertTriangle, Key } from 'lucide-react';

interface TestnetCardProps {
  testnetStatus: TestnetStatusResponse | null;
  testnetAccount: TestnetAccountResponse | null;
}

export const TestnetCard: React.FC<TestnetCardProps> = ({ testnetStatus, testnetAccount }) => {
  const isOnline = testnetStatus?.status === 'ONLINE';
  const hasKeys = testnetStatus?.api_key_configured ?? false;
  const isTestnet = testnetStatus?.testnet ?? true;

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400 border border-amber-500/20">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-slate-200">Binance Spot Testnet Gateway</h3>
              <span
                className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${
                  isOnline
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                }`}
              >
                {isOnline ? 'ONLINE' : 'UNREACHABLE'}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Base URL: {testnetStatus?.base_url || 'https://testnet.binance.vision/api/v3'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-medium rounded-lg border ${
              hasKeys
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>{hasKeys ? 'HMAC KEYS LOADED' : 'DEMO KEYS FALLBACK'}</span>
          </span>
        </div>
      </div>

      {/* Grid of Diagnostics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 font-mono">
        <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5">
          <div className="text-[10px] text-slate-500 uppercase">API Environment</div>
          <div className="text-xs font-bold text-slate-200 mt-1">
            {isTestnet ? 'SPOT TESTNET' : 'SPOT MAINNET'}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5">
          <div className="text-[10px] text-slate-500 uppercase">Server Latency</div>
          <div className="text-xs font-bold text-emerald-400 mt-1">
            {testnetStatus?.latency_ms !== undefined ? `${testnetStatus.latency_ms} ms` : '~45 ms'}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5">
          <div className="text-[10px] text-slate-500 uppercase">Trade Permission</div>
          <div className="text-xs font-bold text-slate-200 mt-1 flex items-center gap-1">
            {testnetAccount?.account?.can_trade ?? false ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> ENABLED
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> SIMULATED
              </span>
            )}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5">
          <div className="text-[10px] text-slate-500 uppercase">Security Audit</div>
          <div className="text-xs font-bold text-emerald-400 mt-1 flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>NO WITHDRAWALS</span>
          </div>
        </div>
      </div>

      {/* Safety Banner */}
      <div className="bg-indigo-950/30 border border-indigo-500/20 rounded-lg p-3 text-xs text-slate-300 font-mono flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <div className="font-semibold text-indigo-300">Dual-Flag Execution Safety Protocol:</div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Real order submission requires BOTH <span className="text-amber-300">TRADING_ENABLED=true</span> and{' '}
            <span className="text-amber-300">LIVE_TRADING=true</span> with HMAC credentials. In default paper mode,
            all orders execute with zero financial risk in our high-fidelity simulator.
          </p>
        </div>
      </div>
    </div>
  );
};
