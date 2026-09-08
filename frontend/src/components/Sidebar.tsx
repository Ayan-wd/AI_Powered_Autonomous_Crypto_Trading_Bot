import React from 'react';
import {
  Activity,
  BarChart3,
  TrendingUp,
  Cpu,
  Shield,
  Wallet,
  FileText,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';
import type { TickerResponse } from '../services/api';

export interface CoinWatchItem {
  symbol: string;
  name: string;
  shortName: string;
  iconBg: string;
}

export const SUPPORTED_COIN_LIST: CoinWatchItem[] = [
  { symbol: 'BTCUSDT', name: 'Bitcoin', shortName: 'BTC', iconBg: 'bg-zinc-800 text-white' },
  { symbol: 'ETHUSDT', name: 'Ethereum', shortName: 'ETH', iconBg: 'bg-zinc-800 text-white' },
  { symbol: 'SOLUSDT', name: 'Solana', shortName: 'SOL', iconBg: 'bg-zinc-800 text-white' },
  { symbol: 'BNBUSDT', name: 'BNB Chain', shortName: 'BNB', iconBg: 'bg-zinc-800 text-white' },
  { symbol: 'DOGEUSDT', name: 'Dogecoin', shortName: 'DOGE', iconBg: 'bg-zinc-800 text-white' },
  { symbol: 'ADAUSDT', name: 'Cardano', shortName: 'ADA', iconBg: 'bg-zinc-800 text-white' },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  watchlistMap: Record<string, TickerResponse>;
  wsConnected: boolean;
  isDaemonRunning: boolean;
  tradingMode: string;
  isOpen: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  selectedSymbol,
  onSelectSymbol,
  watchlistMap,
  wsConnected,
  isDaemonRunning,
  tradingMode,
  isOpen,
  onToggle,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'chart', label: 'Live Graph', icon: TrendingUp, badge: 'LIVE' },
    { id: 'bot', label: 'Bot Engine', icon: Cpu },
    { id: 'position', label: 'Active Position', icon: Zap },
    { id: 'risk', label: 'Risk Guardrails', icon: Shield },
    { id: 'testnet', label: 'Testnet Gateway', icon: Wallet },
    { id: 'trades', label: 'Trade Ledger', icon: FileText },
  ];

  const formatPrice = (price?: number) => {
    if (price === undefined || price === null || isNaN(price)) return '---';
    if (price >= 1000) return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (price >= 1) return `$${price.toFixed(3)}`;
    return `$${price.toFixed(4)}`;
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          onClick={onToggle}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 bg-[#09090b] border-r border-zinc-800 text-zinc-100 flex flex-col transition-all duration-300 ease-in-out ${
          isOpen ? 'w-64 translate-x-0' : 'w-16 -translate-x-full lg:translate-x-0 lg:w-16'
        }`}
      >
        {/* Top Header / Brand */}
        <div className="h-16 border-b border-zinc-800 px-4 flex items-center justify-between">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-white text-black flex items-center justify-center font-black shadow-[0_0_15px_rgba(255,255,255,0.3)] shrink-0">
              <Activity className="w-4 h-4 text-black stroke-[2.5]" />
            </div>
            {isOpen && (
              <div className="truncate">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold tracking-wider text-white">QUANTUM</span>
                  <span className="text-[10px] bg-zinc-800 text-zinc-300 font-mono px-1.5 py-0.2 rounded border border-zinc-700">PRO</span>
                </div>
                <p className="text-[11px] text-zinc-400 font-mono">Algorithmic Spot</p>
              </div>
            )}
          </div>

          <button
            onClick={onToggle}
            className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition"
            title={isOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
          >
            {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-2 py-3 border-b border-zinc-800/80 space-y-1">
          {isOpen && (
            <div className="px-2 pb-1.5 text-[10px] font-semibold text-zinc-400 uppercase tracking-wider font-mono">
              Platform Views
            </div>
          )}
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all group relative ${
                  isActive
                    ? 'bg-white text-black shadow-sm font-semibold'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
                }`}
                title={!isOpen ? item.label : undefined}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-black stroke-[2.2]' : 'text-zinc-400 group-hover:text-white'}`} />
                {isOpen && (
                  <div className="flex items-center justify-between w-full">
                    <span className="truncate">{item.label}</span>
                    {item.badge && (
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${isActive ? 'bg-black text-white' : 'bg-white/10 text-white border border-white/20'}`}>
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Live Added Coins Watchlist */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
          {isOpen ? (
            <>
              <div className="px-2 pb-2 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider font-mono">
                    Added Coins (Live)
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <button
                  onClick={() => onSelectSymbol('ALL')}
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border transition ${
                    selectedSymbol === 'ALL'
                      ? 'bg-white text-black font-semibold border-white'
                      : 'bg-zinc-900 text-zinc-400 hover:text-white border-zinc-800'
                  }`}
                  title="Scan all supported coins simultaneously"
                >
                  SCAN ALL
                </button>
              </div>

              <div className="space-y-1">
                {SUPPORTED_COIN_LIST.map((coin) => {
                  const isSelected = selectedSymbol === coin.symbol;
                  const data = watchlistMap[coin.symbol];
                  const priceChange = data?.price_change_24h_pct ?? 0;
                  const isPositive = priceChange >= 0;

                  return (
                    <button
                      key={coin.symbol}
                      onClick={() => onSelectSymbol(coin.symbol)}
                      className={`w-full text-left p-2 rounded-lg border transition flex items-center justify-between ${
                        isSelected
                          ? 'bg-zinc-900 border-zinc-600 text-white shadow-sm ring-1 ring-white/20'
                          : 'bg-zinc-950/60 border-zinc-800/80 hover:border-zinc-700 text-zinc-300 hover:bg-zinc-900/60'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <div
                          className={`w-7 h-7 rounded-md flex items-center justify-center font-mono text-[11px] font-bold shrink-0 ${
                            isSelected ? 'bg-white text-black' : 'bg-zinc-800 text-zinc-200 border border-zinc-700'
                          }`}
                        >
                          {coin.shortName.slice(0, 3)}
                        </div>
                        <div className="truncate">
                          <div className="flex items-center gap-1">
                            <span className="text-xs font-bold text-white truncate">{coin.shortName}</span>
                            <span className="text-[10px] text-zinc-400 font-mono">/USDT</span>
                          </div>
                          <span className="text-[10px] text-zinc-400 truncate block">{coin.name}</span>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-xs font-mono font-bold text-white">
                          {formatPrice(data?.price)}
                        </div>
                        <div
                          className={`text-[10px] font-mono font-medium ${
                            isPositive ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isPositive ? '+' : ''}
                          {priceChange.toFixed(2)}%
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          ) : (
            // Collapsed coin icons
            <div className="space-y-1.5 pt-2 flex flex-col items-center">
              <button
                onClick={() => onSelectSymbol('ALL')}
                className={`w-9 h-9 rounded-lg flex items-center justify-center text-[10px] font-mono font-bold border transition ${
                  selectedSymbol === 'ALL'
                    ? 'bg-white text-black border-white'
                    : 'bg-zinc-900 text-zinc-400 hover:text-white border-zinc-800'
                }`}
                title="Scan All Coins"
              >
                ALL
              </button>
              {SUPPORTED_COIN_LIST.map((coin) => {
                const isSelected = selectedSymbol === coin.symbol;
                return (
                  <button
                    key={coin.symbol}
                    onClick={() => onSelectSymbol(coin.symbol)}
                    className={`w-9 h-9 rounded-lg flex items-center justify-center text-[10px] font-mono font-bold border transition ${
                      isSelected
                        ? 'bg-white text-black border-white ring-1 ring-white'
                        : 'bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 border-zinc-800'
                    }`}
                    title={`${coin.name} (${coin.symbol})`}
                  >
                    {coin.shortName.slice(0, 3)}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Sidebar Footer / System Status */}
        <div className="p-3 border-t border-zinc-800 bg-black/60">
          {isOpen ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400 font-mono">Engine Daemon</span>
                <span
                  className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] ${
                    isDaemonRunning
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                  }`}
                >
                  {isDaemonRunning ? 'RUNNING' : 'IDLE'}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400 font-mono">Mode</span>
                <span className="text-white font-mono font-semibold">{tradingMode}</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400 font-mono">Live Stream</span>
                <span className="flex items-center gap-1.5 text-zinc-300 font-mono text-[10px]">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-500'
                    }`}
                  />
                  {wsConnected ? 'CONNECTED' : 'DISCONNECTED'}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  isDaemonRunning ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'
                }`}
                title={`Engine Daemon: ${isDaemonRunning ? 'RUNNING' : 'IDLE'}`}
              />
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
