export type TradingMode = 'PAPER' | 'TESTNET' | 'LIVE';
export type BotState = 'RUNNING' | 'STOPPED' | 'PAUSED' | 'EMERGENCY_STOP';

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  timestamp: string;
  project: string;
  version: string;
  mode: TradingMode;
  trading_enabled: boolean;
  database: string;
  environment: string;
}

export interface BotStatus {
  bot_state: BotState;
  trading_mode: TradingMode;
  trading_enabled: boolean;
  live_trading_allowed: boolean;
  kill_switch_active: boolean;
  symbol: string;
  timeframe: string;
  uptime_since: string;
  daily_trades_count: number;
  max_daily_trades: number;
  daily_loss_usd: number;
  max_daily_loss_pct: number;
  last_signal: string;
  last_signal_time: string | null;
}

export interface AccountSummary {
  starting_capital: number;
  total_equity: number;
  available_balance: number;
  base_currency: string;
  unrealized_pnl: number;
  realized_pnl: number;
  net_profit: number;
  return_pct: number;
  drawdown_pct: number;
  max_drawdown_limit_pct: number;
  mode: TradingMode;
  open_positions: any[];
}

export interface TradeItem {
  id: number;
  trade_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  entry_time: string | null;
  exit_time: string | null;
  pnl: number;
  pnl_pct: number;
  fees: number;
  slippage: number;
  stop_loss: number | null;
  take_profit: number | null;
  model_probability: number | null;
  strategy_reason: string | null;
  explanation_json: string | null;
  status: 'OPEN' | 'CLOSED' | 'CANCELED';
  is_paper: boolean;
}

export interface TradeMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  gross_profit: number;
  gross_loss: number;
  net_pnl: number;
  total_fees: number;
  avg_trade_pnl: number;
  largest_win: number;
  largest_loss: number;
}

export interface MarketDataSnapshot {
  symbol: string;
  price: number;
  price_change_24h_pct: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  ema_20: number;
  ema_50: number;
  ema_200: number;
  atr_14: number;
  volume_24h: number;
  volatility_regime: 'LOW' | 'NORMAL' | 'HIGH';
  trend_regime: 'BULLISH' | 'BEARISH' | 'RANGING';
}

export interface AIPredictionSnapshot {
  symbol: string;
  timestamp: string;
  decision: 'BUY' | 'SELL' | 'HOLD / NO TRADE';
  probabilities: {
    buy: number;
    sell: number;
    hold: number;
  };
  confidence: number;
  expected_return_pct: number;
  features_summary: {
    rsi: number;
    trend: string;
    volatility: string;
    volume_ratio: number;
  };
  reasoning: string[];
}
