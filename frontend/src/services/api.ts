import type { AccountSummary, BotStatus, HealthResponse, TradeItem, TradeMetrics } from '../types/trading';

const API_BASE = '/api/v1';

export interface TickerResponse {
  symbol: string;
  price: number;
  bid_price: number;
  ask_price: number;
  volume_24h: number;
  price_change_24h_pct: number;
  timestamp: number;
}

export interface CandleResponse {
  id: number;
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  quote_volume: number;
  trades_count: number;
  is_closed: boolean;
}

export interface FeaturesResponse {
  status: string;
  symbol: string;
  timeframe: string;
  timestamp: string;
  price: number;
  rsi_14: number;
  macd: {
    value: number;
    signal: number;
    hist: number;
  };
  ema: {
    ema20: number;
    ema50: number;
    ema200: number;
  };
  bollinger: {
    upper: number;
    middle: number;
    lower: number;
    width: number;
  };
  atr_14: number;
  returns: {
    return_1p: number;
    return_3p: number;
    return_5p: number;
  };
  regimes: {
    trend: 'BULLISH' | 'BEARISH' | 'RANGING';
    volatility: 'HIGH' | 'LOW' | 'NORMAL';
  };
  message?: string;
}

export interface MLPredictionResponse {
  status: string;
  symbol: string;
  timestamp: string;
  decision: 'BUY' | 'SELL' | 'HOLD / NO TRADE';
  probabilities: {
    buy: number;
    sell: number;
    hold: number;
  };
  confidence: number;
  confidence_threshold: number;
  expected_return_pct: number;
  model_version: string;
  reasoning: string[];
  features_snapshot?: Record<string, number>;
  message?: string;
}

export interface BenchmarkResponse {
  status: string;
  symbol: string;
  timeframe: string;
  candle_count: number;
  starting_capital: number;
  strategies: {
    buy_and_hold: Record<string, any>;
    technical_cross: Record<string, any>;
    ai_multi_factor: Record<string, any>;
  };
  comparison: {
    best_return_strategy: string;
    lowest_drawdown_strategy: string;
  };
  message?: string;
}

export interface RiskStatusResponse {
  trading_permitted: boolean;
  denial_reason: string | null;
  current_equity: number;
  high_water_mark: number;
  drawdown_pct: number;
  max_drawdown_limit_pct: number;
  daily_loss_usd: number;
  daily_loss_pct: number;
  max_daily_loss_limit_pct: number;
  weekly_loss_usd: number;
  consecutive_losses: number;
  max_consecutive_losses_limit: number;
  daily_trades_count: number;
  max_daily_trades: number;
  circuit_breaker_active: boolean;
  max_risk_per_trade_pct: number;
  max_position_size_usd: number;
  starting_capital: number;
}

export interface StrategyDecisionResponse {
  action: 'BUY' | 'SELL' | 'HOLD / NO TRADE';
  reason: string;
  confidence: number;
  order_details: {
    side: 'BUY' | 'SELL';
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    position_size_usd: number;
    quantity: number;
    risk_amount_usd: number;
    risk_pct: number;
    risk_reward_ratio: number;
  } | null;
  ml_probabilities?: {
    buy: number;
    sell: number;
    hold: number;
  };
  regime?: {
    trend: string;
    volatility: string;
  };
  numerical_explanation: string[];
  symbol?: string;
  timeframe?: string;
  account_equity?: number;
}

export interface ActivePosition {
  trade_id: string;
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number;
  quantity: number;
  position_value_usd: number;
  cost_basis_usd: number;
  unrealized_pnl_usd: number;
  unrealized_pnl_pct: number;
  stop_loss: number | null;
  take_profit: number | null;
  highest_price: number;
  entry_time: string;
  model_probability?: number;
  strategy_reason?: string;
}

export interface TestnetStatusResponse {
  status: string;
  testnet: boolean;
  base_url: string;
  server_time?: number;
  latency_ms?: number;
  api_key_configured: boolean;
  trading_mode: string;
  trading_enabled: boolean;
  live_trading_safety_flag: boolean;
  error?: string;
}

export interface TestnetAccountResponse {
  status: string;
  message?: string;
  can_trade?: boolean;
  can_withdraw?: boolean;
  account?: {
    can_trade: boolean;
    can_withdraw: boolean;
    account_type: string;
    security_audit_passed: boolean;
    balances: Record<string, number>;
  };
}

export interface BotDaemonStatus {
  is_running: boolean;
  symbol: string;
  timeframe: string;
  mode: string;
  iteration_count: number;
  active_position: ActivePosition | null;
  wallet: {
    usdt_balance: number;
    total_equity: number;
    unrealized_pnl: number;
    realized_pnl_total: number;
    total_fees_paid: number;
    has_open_position: boolean;
  };
  risk_snapshot: RiskStatusResponse;
  last_decision: Record<string, any>;
}

export const apiService = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },

  async getBotStatus(): Promise<BotStatus> {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) throw new Error('Failed to fetch bot status');
    return res.json();
  },

  async getAccountSummary(): Promise<AccountSummary> {
    const res = await fetch(`${API_BASE}/account/summary`);
    if (!res.ok) throw new Error('Failed to fetch account summary');
    return res.json();
  },

  async getTrades(limit = 50, offset = 0): Promise<TradeItem[]> {
    const res = await fetch(`${API_BASE}/trades?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to fetch trades');
    return res.json();
  },

  async getTradeMetrics(): Promise<TradeMetrics> {
    const res = await fetch(`${API_BASE}/trades/metrics`);
    if (!res.ok) throw new Error('Failed to fetch trade metrics');
    return res.json();
  },

  async getTicker(symbol = 'BTCUSDT'): Promise<TickerResponse> {
    const res = await fetch(`${API_BASE}/market/ticker?symbol=${symbol}`);
    if (!res.ok) throw new Error('Failed to fetch ticker');
    return res.json();
  },

  async getCandles(symbol = 'BTCUSDT', timeframe = '15m', limit = 100): Promise<CandleResponse[]> {
    const res = await fetch(`${API_BASE}/market/candles?symbol=${symbol}&timeframe=${timeframe}&limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch candles');
    return res.json();
  },

  async syncCandles(symbol = 'BTCUSDT', timeframe = '15m', limit = 300): Promise<any> {
    const res = await fetch(`${API_BASE}/market/sync?symbol=${symbol}&timeframe=${timeframe}&limit=${limit}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to sync candles');
    return res.json();
  },

  async getLatestFeatures(symbol = 'BTCUSDT', timeframe = '15m'): Promise<FeaturesResponse> {
    const res = await fetch(`${API_BASE}/features/latest?symbol=${symbol}&timeframe=${timeframe}`);
    if (!res.ok) throw new Error('Failed to fetch features');
    return res.json();
  },

  async getMLPrediction(symbol = 'BTCUSDT', timeframe = '15m'): Promise<MLPredictionResponse> {
    const res = await fetch(`${API_BASE}/ml/predict?symbol=${symbol}&timeframe=${timeframe}`);
    if (!res.ok) throw new Error('Failed to fetch ML prediction');
    return res.json();
  },

  async trainModel(symbol = 'BTCUSDT', timeframe = '15m', limitCandles = 500): Promise<any> {
    const res = await fetch(`${API_BASE}/ml/train?symbol=${symbol}&timeframe=${timeframe}&limit_candles=${limitCandles}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to train model');
    return res.json();
  },

  async runBenchmark(symbol = 'BTCUSDT', timeframe = '15m', limitCandles = 300): Promise<BenchmarkResponse> {
    const res = await fetch(`${API_BASE}/backtest/benchmark?symbol=${symbol}&timeframe=${timeframe}&limit_candles=${limitCandles}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to run benchmark');
    return res.json();
  },

  async triggerKillSwitch(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/status/kill-switch`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger kill switch');
    return res.json();
  },

  async resetKillSwitch(): Promise<{ status: string; bot_state: string }> {
    const res = await fetch(`${API_BASE}/status/reset-kill-switch`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset kill switch');
    return res.json();
  },

  async getRiskStatus(): Promise<RiskStatusResponse> {
    const res = await fetch(`${API_BASE}/risk/status`);
    if (!res.ok) throw new Error('Failed to fetch risk status');
    return res.json();
  },

  async getStrategyDecision(symbol = 'BTCUSDT', timeframe = '15m'): Promise<StrategyDecisionResponse> {
    const res = await fetch(`${API_BASE}/strategy/decision?symbol=${symbol}&timeframe=${timeframe}`);
    if (!res.ok) throw new Error('Failed to fetch strategy decision');
    return res.json();
  },

  async getBotDaemonStatus(): Promise<BotDaemonStatus> {
    const res = await fetch(`${API_BASE}/trading/bot/status`);
    if (!res.ok) throw new Error('Failed to fetch bot daemon status');
    return res.json();
  },

  async startBot(symbol = 'BTCUSDT', timeframe = '15m'): Promise<any> {
    const res = await fetch(`${API_BASE}/trading/bot/start?symbol=${symbol}&timeframe=${timeframe}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to start bot');
    return res.json();
  },

  async stopBot(): Promise<any> {
    const res = await fetch(`${API_BASE}/trading/bot/stop`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to stop bot');
    return res.json();
  },

  async getActivePosition(): Promise<{ active_position: ActivePosition | null; has_open_position: boolean }> {
    const res = await fetch(`${API_BASE}/trading/position`);
    if (!res.ok) throw new Error('Failed to fetch active position');
    return res.json();
  },

  async closePositionManually(reason = 'MANUAL_CLOSE'): Promise<any> {
    const res = await fetch(`${API_BASE}/trading/position/close?reason=${reason}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to close position');
    return res.json();
  },

  async resetPaperTrading(startingCapital = 50.0): Promise<any> {
    const res = await fetch(`${API_BASE}/trading/paper/reset?starting_capital=${startingCapital}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to reset paper trading');
    return res.json();
  },

  async getTestnetStatus(): Promise<TestnetStatusResponse> {
    const res = await fetch(`${API_BASE}/testnet/status`);
    if (!res.ok) throw new Error('Failed to fetch testnet status');
    return res.json();
  },

  async getTestnetAccount(): Promise<TestnetAccountResponse> {
    const res = await fetch(`${API_BASE}/testnet/account`);
    if (!res.ok) throw new Error('Failed to fetch testnet account');
    return res.json();
  },

  async getPerformanceAnalytics(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/performance`);
    if (!res.ok) throw new Error('Failed to fetch performance analytics');
    return res.json();
  },

  async getSecurityAudit(): Promise<any> {
    const res = await fetch(`${API_BASE}/security/audit`);
    if (!res.ok) throw new Error('Failed to fetch security audit');
    return res.json();
  },

  async getConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch config');
    return res.json();
  },
};
