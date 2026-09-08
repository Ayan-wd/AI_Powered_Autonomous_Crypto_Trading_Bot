import React from 'react';
import type { TestnetAccountResponse, TestnetStatusResponse } from '../services/api';
import { Globe, ShieldCheck, CheckCircle2, Key } from 'lucide-react';

interface TestnetCardProps {
  testnetStatus: TestnetStatusResponse | null;
  testnetAccount: TestnetAccountResponse | null;
}

export const TestnetCard: React.FC<TestnetCardProps> = ({ testnetStatus, testnetAccount }) => {
  const isOnline = testnetStatus?.status === 'ONLINE';
  const hasKeys = testnetStatus?.api_key_configured ?? false;
  const isTestnet = testnetStatus?.testnet ?? true;

  const balances = testnetAccount?.account?.balances || {};
  const balanceEntries = Object.entries(balances);

  return (
    <div className="bg-[#09090b] border border-zinc-800 rounded-xl p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-black rounded-lg text-white border border-zinc-800">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-white">Binance Spot Testnet Gateway</h3>
              <span
                className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${
                  isOnline
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                }`}
              >
                {isOnline ? 'ONLINE' : 'UNREACHABLE'}
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              Endpoint: {testnetStatus?.base_url || 'https://testnet.binance.vision/api/v3'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-medium rounded-lg border ${
              hasKeys
                ? 'bg-white text-black border-white font-bold'
                : 'bg-zinc-900 text-zinc-400 border-zinc-800'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>{hasKeys ? 'HMAC KEYS LOADED' : 'DEMO KEYS FALLBACK'}</span>
          </span>
        </div>
      </div>

      {/* Grid of Diagnostics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 font-mono">
        <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
          <div className="text-[10px] text-zinc-400 uppercase">API Environment</div>
          <div className="text-xs font-bold text-white mt-1">
            {isTestnet ? 'Binance Spot Testnet' : 'Live Production'}
          </div>
        </div>

        <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
          <div className="text-[10px] text-zinc-400 uppercase">Account Status</div>
          <div className="text-xs font-bold text-white mt-1">
            {testnetAccount?.account?.account_type || 'SPOT ACCOUNT'}
          </div>
        </div>

        <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
          <div className="text-[10px] text-zinc-400 uppercase">Trading Permissions</div>
          <div className="text-xs font-bold text-emerald-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>SPOT_PERMITTED</span>
          </div>
        </div>

        <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-3">
          <div className="text-[10px] text-zinc-400 uppercase">Order Execution Mode</div>
          <div className="text-xs font-bold text-white mt-1">
            HMAC-SHA256 SIGNED
          </div>
        </div>
      </div>

      {/* Account Balances List if Available */}
      {balanceEntries.length > 0 && (
        <div className="mt-2 pt-3 border-t border-zinc-900">
          <div className="text-[10px] uppercase text-zinc-400 font-mono mb-2 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
            <span>Testnet Balances Portfolio</span>
          </div>
          <div className="flex flex-wrap gap-2 font-mono">
            {balanceEntries.map(([asset, free]) => (
              <div
                key={asset}
                className="bg-black border border-zinc-800 rounded-md px-3 py-1.5 text-xs flex items-center gap-2"
              >
                <span className="font-bold text-white">{asset}:</span>
                <span className="text-zinc-300">
                  {typeof free === 'number' ? free.toLocaleString(undefined, { maximumFractionDigits: 4 }) : free}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
