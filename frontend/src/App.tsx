import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { BotControlBar } from './components/BotControlBar';
import { ActivePositionCard } from './components/ActivePositionCard';
import { TestnetCard } from './components/TestnetCard';
import { SecurityAuditCard } from './components/SecurityAuditCard';
import { AnalyticsCard } from './components/AnalyticsCard';
import { MetricCards } from './components/MetricCards';
import { AIPredictionCard } from './components/AIPredictionCard';
import { MarketOverviewCard } from './components/MarketOverviewCard';
import { RiskStrategyCard } from './components/RiskStrategyCard';
import { BenchmarkCard } from './components/BenchmarkCard';
import { TradesTable } from './components/TradesTable';
import { EquityChart } from './components/EquityChart';
import {
  apiService,
  type ActivePosition,
  type BenchmarkResponse,
  type BotDaemonStatus,
  type FeaturesResponse,
  type MLPredictionResponse,
  type RiskStatusResponse,
  type StrategyDecisionResponse,
  type TestnetAccountResponse,
  type TestnetStatusResponse,
  type TickerResponse,
} from './services/api';
import { wsClient } from './services/websocket';
import type { AccountSummary, BotStatus, TradeItem, TradeMetrics } from './types/trading';
import { AlertCircle, Terminal } from 'lucide-react';

export function App() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [trades, setTrades] = useState<TradeItem[]>([]);
  const [metrics, setMetrics] = useState<TradeMetrics | null>(null);
  const [ticker, setTicker] = useState<TickerResponse | null>(null);
  const [features, setFeatures] = useState<FeaturesResponse | null>(null);
  const [prediction, setPrediction] = useState<MLPredictionResponse | null>(null);
  const [riskStatus, setRiskStatus] = useState<RiskStatusResponse | null>(null);
  const [strategyDecision, setStrategyDecision] = useState<StrategyDecisionResponse | null>(null);
  const [botDaemon, setBotDaemon] = useState<BotDaemonStatus | null>(null);
  const [activePosition, setActivePosition] = useState<ActivePosition | null>(null);
  const [testnetStatus, setTestnetStatus] = useState<TestnetStatusResponse | null>(null);
  const [testnetAccount, setTestnetAccount] = useState<TestnetAccountResponse | null>(null);
  const [securityAudit, setSecurityAudit] = useState<any | null>(null);
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [syncingCandles, setSyncingCandles] = useState<boolean>(false);
  const [trainingModel, setTrainingModel] = useState<boolean>(false);
  const [evaluatingStrategy, setEvaluatingStrategy] = useState<boolean>(false);
  const [runningBenchmark, setRunningBenchmark] = useState<boolean>(false);
  const [botActionLoading, setBotActionLoading] = useState<boolean>(false);
  const [closingPosition, setClosingPosition] = useState<boolean>(false);
  const [resettingPaper, setResettingPaper] = useState<boolean>(false);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('1m');

  const fetchData = async () => {
    try {
      setLoading(true);
      const symbol = selectedSymbol === 'ALL' ? 'BTCUSDT' : (botDaemon?.symbol && botDaemon.symbol !== 'ALL' ? botDaemon.symbol : selectedSymbol);
      const timeframe = botDaemon?.timeframe || selectedTimeframe;

      const [
        statusRes,
        accountRes,
        tradesRes,
        metricsRes,
        tickerRes,
        featuresRes,
        predRes,
        riskRes,
        stratRes,
        daemonRes,
        posRes,
        tnetStatusRes,
        tnetAccRes,
        analyticsRes,
        securityRes,
      ] = await Promise.all([
        apiService.getBotStatus(),
        apiService.getAccountSummary(),
        apiService.getTrades(50),
        apiService.getTradeMetrics(),
        apiService.getTicker(symbol).catch(() => null),
        apiService.getLatestFeatures(symbol, timeframe).catch(() => null),
        apiService.getMLPrediction(symbol, timeframe).catch(() => null),
        apiService.getRiskStatus().catch(() => null),
        apiService.getStrategyDecision(symbol, timeframe).catch(() => null),
        apiService.getBotDaemonStatus().catch(() => null),
        apiService.getActivePosition().catch(() => null),
        apiService.getTestnetStatus().catch(() => null),
        apiService.getTestnetAccount().catch(() => null),
        apiService.getPerformanceAnalytics().catch(() => null),
        apiService.getSecurityAudit().catch(() => null),
      ]);
      setStatus(statusRes);
      setAccount(accountRes);
      setTrades(tradesRes);
      setMetrics(metricsRes);
      if (tickerRes) setTicker(tickerRes);
      if (featuresRes && featuresRes.status === 'OK') setFeatures(featuresRes);
      if (predRes && predRes.status === 'OK') setPrediction(predRes);
      if (riskRes) setRiskStatus(riskRes);
      if (stratRes) setStrategyDecision(stratRes);
      if (daemonRes) setBotDaemon(daemonRes);
      if (posRes) setActivePosition(posRes.active_position);
      if (tnetStatusRes) setTestnetStatus(tnetStatusRes);
      if (tnetAccRes) setTestnetAccount(tnetAccRes);
      if (analyticsRes) setAnalytics(analyticsRes);
      if (securityRes) setSecurityAudit(securityRes);
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

    // WebSocket real-time connection
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((event, data) => {
      if (event === 'CONNECTION_OPEN') {
        setWsConnected(true);
      } else if (event === 'CONNECTION_CLOSED') {
        setWsConnected(false);
      } else if (event === 'TICKER_UPDATE' && data) {
        setTicker((prev) => (prev ? { ...prev, ...data } : data));
      } else if (event === 'POSITION_UPDATE') {
        setActivePosition(data);
      } else if (event === 'STRATEGY_DECISION') {
        setStrategyDecision(data);
      } else if (event === 'ORDER_FILLED' || event === 'POSITION_CLOSED') {
        fetchData();
      }
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
      wsClient.disconnect();
    };
  }, []);

  const handleStartBot = async (sym?: string, tf?: string) => {
    try {
      setBotActionLoading(true);
      const targetSym = sym || selectedSymbol;
      const targetTf = tf || selectedTimeframe;
      await apiService.startBot(targetSym, targetTf);
      await fetchData();
    } catch (e: any) {
      alert('Error starting bot: ' + e.message);
    } finally {
      setBotActionLoading(false);
    }
  };

  const handleStopBot = async () => {
    try {
      setBotActionLoading(true);
      await apiService.stopBot();
      await fetchData();
    } catch (e: any) {
      alert('Error stopping bot: ' + e.message);
    } finally {
      setBotActionLoading(false);
    }
  };

  const handleClosePosition = async () => {
    try {
      setClosingPosition(true);
      const res = await apiService.closePositionManually('MANUAL_CLOSE');
      alert(res.message || 'Position closed successfully.');
      await fetchData();
    } catch (e: any) {
      alert('Error closing position: ' + e.message);
    } finally {
      setClosingPosition(false);
    }
  };

  const handleResetPaper = async () => {
    if (!confirm('Are you sure you want to reset paper trading capital back to $50.00 USD?')) {
      return;
    }
    try {
      setResettingPaper(true);
      const res = await apiService.resetPaperTrading(50.0);
      alert(res.message || 'Paper trading reset complete.');
      await fetchData();
    } catch (e: any) {
      alert('Error resetting paper trading: ' + e.message);
    } finally {
      setResettingPaper(false);
    }
  };

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

  const handleTrainModel = async () => {
    try {
      setTrainingModel(true);
      const res = await apiService.trainModel(status?.symbol || 'BTCUSDT', status?.timeframe || '15m', 500);
      if (res.status === 'TRAINING_COMPLETE') {
        alert(`Model Training Complete! Version: ${res.model_version}\nAverage Walk-Forward Accuracy: ${(res.average_val_accuracy * 100).toFixed(1)}%`);
      } else {
        alert(`Model Training: ${res.message || res.status}`);
      }
      await fetchData();
    } catch (e: any) {
      alert('Training Error: ' + e.message);
    } finally {
      setTrainingModel(false);
    }
  };

  const handleEvaluateStrategy = async () => {
    try {
      setEvaluatingStrategy(true);
      const res = await apiService.getStrategyDecision(status?.symbol || 'BTCUSDT', status?.timeframe || '15m');
      setStrategyDecision(res);
      const risk = await apiService.getRiskStatus();
      setRiskStatus(risk);
    } catch (e: any) {
      alert('Strategy Evaluation Error: ' + e.message);
    } finally {
      setEvaluatingStrategy(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setRunningBenchmark(true);
      const res = await apiService.runBenchmark(status?.symbol || 'BTCUSDT', status?.timeframe || '15m', 300);
      if (res.status === 'SUCCESS') {
        setBenchmark(res);
      } else {
        alert(`Benchmark Notice: ${res.message}`);
      }
    } catch (e: any) {
      alert('Benchmark Error: ' + e.message);
    } finally {
      setRunningBenchmark(false);
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
        wsConnected={wsConnected}
        isDaemonRunning={botDaemon?.is_running ?? false}
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
        {/* Autonomous Bot Control Bar */}
        <BotControlBar
          botDaemon={botDaemon}
          onStartBot={handleStartBot}
          onStopBot={handleStopBot}
          loading={botActionLoading}
          selectedSymbol={selectedSymbol}
          onSymbolChange={setSelectedSymbol}
          selectedTimeframe={selectedTimeframe}
          onTimeframeChange={setSelectedTimeframe}
        />

        {/* Metric Cards Banner */}
        <MetricCards account={account} metrics={metrics} />

        {/* Institutional Performance Analytics Card */}
        <AnalyticsCard analytics={analytics} />

        {/* Active Paper Position Card */}
        <ActivePositionCard
          position={activePosition}
          onClosePosition={handleClosePosition}
          onResetPaper={handleResetPaper}
          closing={closingPosition}
          resetting={resettingPaper}
        />

        {/* Binance Spot Testnet Gateway */}
        <TestnetCard
          testnetStatus={testnetStatus}
          testnetAccount={testnetAccount}
        />

        {/* Security, Hardening & Resilience Audit */}
        <SecurityAuditCard auditData={securityAudit} />

        {/* Risk & Strategy Gatekeeper */}
        <RiskStrategyCard
          riskStatus={riskStatus}
          strategyDecision={strategyDecision}
          onEvaluateStrategy={handleEvaluateStrategy}
          loading={evaluatingStrategy}
        />

        {/* Middle Two-Column Grid: AI Prediction + Market Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AIPredictionCard
            symbol={status?.symbol || 'BTC/USDT'}
            prediction={prediction}
            onTrainModel={handleTrainModel}
            training={trainingModel}
          />
          <MarketOverviewCard
            symbol={status?.symbol || 'BTCUSDT'}
            ticker={ticker}
            features={features}
            onSyncCandles={handleSyncCandles}
            syncing={syncingCandles}
          />
        </div>

        {/* 3-Way Strategy Benchmark Comparator */}
        <BenchmarkCard
          benchmark={benchmark}
          onRunBenchmark={handleRunBenchmark}
          loading={runningBenchmark}
        />

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
