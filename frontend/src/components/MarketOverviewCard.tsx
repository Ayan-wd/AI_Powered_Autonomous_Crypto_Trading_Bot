import React from 'react';
import { BarChart3, RefreshCw } from 'lucide-react';
import type { FeaturesResponse, TickerResponse } from '../services/api';

interface MarketOverviewProps {
  symbol?: string;
  ticker?: TickerResponse | null;
  features?: FeaturesResponse | null;
  onSyncCandles?: () => void;
  syncing?: boolean;
}

export const MarketOverviewCard: React.FC<MarketOverviewProps> = ({
  symbol = 'BTCUSDT',
  ticker,
  features,
  onSyncCandles,
  syncing = false,
}) => {
  const price = features?.price ?? ticker?.price ?? 91845.20;
  const change24h = ticker?.price_change_24h_pct ?? 1.42;

  const rsi = features?.rsi_14 ?? 52.8;
  const macdHist = features?.macd?.hist ?? 14.2;
  const atr = features?.atr_14 ?? 450.2;
  const volRegime = features?.regimes?.volatility ?? 'NORMAL';
  const trendRegime = features?.regimes?.trend ?? 'BULLISH';

  const ema20 = features?.ema?.ema20 ?? price * 0.998;
  const ema50 = features?.ema?.ema50 ?? price * 0.994;
  const ema200 = features?.ema?.ema200 ?? price * 0.975;

  return (
    <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white">Live Market Analysis ({symbol})</h3>
              {onSyncCandles && (
                <button
                  onClick={onSyncCandles}
                  disabled={syncing}
                  className="px-2 py-0.5 text-[10px] font-medium text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-700/50 rounded flex items-center gap-1 transition cursor-pointer"
                  title="Ingest historical candles from Binance into DB"
                >
                  <RefreshCw className={`w-2.5 h-2.5 ${syncing ? 'animate-spin' : ''}`} />
                  <span>Sync Candles</span>
                </button>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono">15-Minute Multi-Indicator Feed</p>
          </div>
        </div>

        <div className="text-right">
          <div className="text-base font-bold text-white font-mono">
            ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span
            className={`text-xs font-semibold ${
              change24h >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {change24h >= 0 ? '+' : ''}{change24h.toFixed(2)}% (24h)
          </span>
        </div>
      </div>

      {/* Grid of indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-4">
        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-0.5">RSI (14)</span>
          <span className={`text-sm font-bold font-mono ${rsi > 70 ? 'text-rose-400' : rsi < 30 ? 'text-emerald-400' : 'text-slate-200'}`}>
            {rsi.toFixed(1)}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-0.5">MACD Hist</span>
          <span className={`text-sm font-bold font-mono ${macdHist >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {macdHist >= 0 ? '+' : ''}{macdHist.toFixed(1)}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-0.5">ATR (14)</span>
          <span className="text-sm font-bold text-slate-200 font-mono">${atr.toFixed(1)}</span>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-0.5">Volatility</span>
          <span className="text-xs font-bold text-cyan-300 font-mono uppercase">{volRegime}</span>
        </div>
      </div>

      {/* EMA Structure */}
      <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80">
        <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center justify-between">
          <span>EMA Trend Structure</span>
          <span className={`font-mono text-[10px] font-bold ${
            trendRegime === 'BULLISH' ? 'text-emerald-400' : trendRegime === 'BEARISH' ? 'text-rose-400' : 'text-amber-400'
          }`}>
            {trendRegime === 'BULLISH'
              ? 'EMA20 > EMA50 > EMA200 (BULLISH)'
              : trendRegime === 'BEARISH'
              ? 'EMA20 < EMA50 < EMA200 (BEARISH)'
              : 'MIXED / RANGING'}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
          <div className="bg-slate-900/80 py-1 px-2 rounded border border-slate-800">
            <span className="text-slate-400 text-[10px] block">EMA 20</span>
            <span className="text-indigo-300 font-semibold">${ema20.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
          </div>
          <div className="bg-slate-900/80 py-1 px-2 rounded border border-slate-800">
            <span className="text-slate-400 text-[10px] block">EMA 50</span>
            <span className="text-indigo-300 font-semibold">${ema50.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
          </div>
          <div className="bg-slate-900/80 py-1 px-2 rounded border border-slate-800">
            <span className="text-slate-400 text-[10px] block">EMA 200</span>
            <span className="text-indigo-300 font-semibold">${ema200.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
