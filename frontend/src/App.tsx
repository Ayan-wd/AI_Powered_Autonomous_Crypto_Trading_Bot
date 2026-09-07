import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { AIPredictionCard } from './components/AIPredictionCard';
import { MarketOverviewCard } from './components/MarketOverviewCard';
import { TradesTable } from './components/TradesTable';
import { EquityChart } from './components/EquityChart';
import { apiService, type FeaturesResponse, type TickerResponse } from './services/api';
import type { AccountSummary, BotStatus, TradeItem, TradeMetrics } from './types/trading';
import { AlertCircle, Terminal } from 'lucide-react';

export function App() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [trades, setTrades] = useState<TradeItem[]>([]);
  const [metrics, setMetrics] = useState<TradeMetrics | null>(null);
  const [ticker, setTicker] = useState<TickerResponse | null>(null);
  const [features, setFeatures] = useState<FeaturesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [syncingCandles, setSyncingCandles] = useState<boolean>(false);
  const [apiConnected, setApiConnected] = useState<boolean>(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const symbol = status?.symbol || 'BTCUSDT';
      const timeframe = status?.timeframe || '15m';

      const [statusRes, accountRes, tradesRes, metricsRes, tickerRes, featuresRes] = await Promise.all([
        apiService.getBotStatus(),
        apiService.getAccountSummary(),
        apiService.getTrades(50),
        apiService.getTradeMetrics(),
        apiService.getTicker(symbol).catch(() => null),
        apiService.getLatestFeatures(symbol, timeframe).catch(() => null),
      ]);
      setStatus(statusRes);
      setAccount(accountRes);
      setTrades(tradesRes);
      setMetrics(metricsRes);
      if (tickerRes) setTicker(tickerRes);
      if (featuresRes && featuresRes.status === 'OK') setFeatures(featuresRes);
      setApiConnected(true);
    } catch (err: any) {
      console.warn('API polling warning:', err);
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSyncCandles = async () => {
    try {
      setSyncingCandles(true);
      const res = await apiService.syncCandles(status?.symbol || 'BTCUSDT', status?.timeframe || '15m', 300);
      alert(`Candle Sync: ${res.message || 'Complete'}`);
      await fetchData();
    } catch (e: any) {
      alert('Candle Sync Error: ' + e.message);
    } finally {
      setSyncingCandles(false);
    }
  };

  const handleKillSwitch = async () => {
    try {
      await apiService.triggerKillSwitch();
      await fetchData();
    } catch (e: any) {
      alert('Error triggering kill switch: ' + e.message);
    }
  };

  const handleResetKillSwitch = async () => {
    try {
      await apiService.resetKillSwitch();
      await fetchData();
    } catch (e: any) {
      alert('Error resetting kill switch: ' + e.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <Header
        status={status}
        onRefresh={fetchData}
        onKillSwitch={handleKillSwitch}
        onResetKillSwitch={handleResetKillSwitch}
        loading={loading}
      />

      {/* Backend connection warning banner if not connected */}
      {!apiConnected && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 animate-pulse" />
            <span>Backend offline / initializing: Starting in standalone preview mode. Launch backend with `uvicorn app.main:app`</span>
          </div>
          <span className="font-mono text-[11px] opacity-75">Target: 127.0.0.1:8000</span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Metric Cards Banner */}
        <MetricCards account={account} metrics={metrics} />

        {/* Middle Two-Column Grid: AI Prediction + Market Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AIPredictionCard
            symbol={status?.symbol || 'BTC/USDT'}
            decision={status?.last_signal || 'HOLD / NO TRADE'}
          />
          <MarketOverviewCard
            symbol={status?.symbol || 'BTCUSDT'}
            ticker={ticker}
            features={features}
            onSyncCandles={handleSyncCandles}
            syncing={syncingCandles}
          />
        </div>

        {/* Equity Curve Tracker */}
        <EquityChart
          startingCapital={account?.starting_capital ?? 50.0}
          currentEquity={account?.total_equity ?? 50.0}
        />

        {/* Audited Trades Ledger */}
        <TradesTable trades={trades} />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-3 text-xs text-slate-500 flex flex-wrap justify-between items-center gap-2">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-indigo-400" />
          <span>Institutional Quantitative Crypto Framework</span>
        </div>
        <div className="flex items-center gap-4 font-mono text-[11px]">
          <span className="text-emerald-400/90 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
            Zero-Leakage ML Pipeline
          </span>
          <span>Capital Limit: $50 USD</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
