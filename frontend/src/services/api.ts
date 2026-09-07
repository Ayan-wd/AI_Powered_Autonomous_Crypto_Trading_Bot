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

  async getConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch config');
    return res.json();
  },
};
