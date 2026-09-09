"""
Technical analysis calculation library.
Vectorized, mathematical implementations for EMAs, RSI, MACD, ATR, Bollinger Bands,
volume dynamics, rolling volatility, and price returns.
Zero-lookahead bias guaranteed.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def compute_sma(series: pd.Series, period: int, min_periods: Optional[int] = None) -> pd.Series:
    """Calculate Simple Moving Average (SMA)."""
    min_p = min_periods if min_periods is not None else period
    return series.rolling(window=period, min_periods=min_p).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI) using Wilder's smoothing method.
    Zero-lookahead bias.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's exponential smoothing (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD).
    Returns (macd_line, signal_line, histogram).
    """
    fast_ema = compute_ema(close, fast_period)
    slow_ema = compute_ema(close, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, signal_period)
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    True Range = max(high - low, abs(high - close_prev), abs(low - close_prev))
    """
    prev_close = close.shift(1).fillna(close)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=1).mean()
    return atr


def compute_bollinger_bands(
    close: pd.Series, period: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    Returns (upper_band, middle_band, lower_band, band_width, pct_b).
    """
    middle = compute_sma(close, period, min_periods=period)
    rolling_std = close.rolling(window=period, min_periods=period).std()
    upper = middle + (num_std * rolling_std)
    lower = middle - (num_std * rolling_std)

    band_width = (upper - lower) / middle.replace(0, np.nan)
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return upper, middle, lower, band_width, pct_b


def compute_returns(close: pd.Series, periods: Tuple[int, ...] = (1, 3, 5, 10)) -> pd.DataFrame:
    """Calculate multi-period percentage returns."""
    df_returns = pd.DataFrame(index=close.index)
    for p in periods:
        df_returns[f"return_{p}p"] = close.pct_change(periods=p)
    return df_returns


def compute_rolling_volatility(returns: pd.Series, windows: Tuple[int, ...] = (14, 30)) -> pd.DataFrame:
    """Calculate rolling standard deviation of 1-period returns as volatility metric."""
    df_vol = pd.DataFrame(index=returns.index)
    for w in windows:
        df_vol[f"volatility_{w}p"] = returns.rolling(window=w, min_periods=w).std()
    return df_vol


def compute_adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Average Directional Index (ADX) and Directional Movement (+DI, -DI).
    Institutional standard for regime identification:
    ADX < 20: Choppy / Sideways consolidation (Suppress trend breakout entries)
    ADX >= 25: Strong trend confirmation
    Returns (adx, plus_di, minus_di).
    """
    prev_high = high.shift(1).fillna(high)
    prev_low = low.shift(1).fillna(low)
    prev_close = close.shift(1).fillna(close)

    # Directional Movement
    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # True Range
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder smoothing (alpha = 1 / period)
    atr_smooth = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    plus_dm_smooth = pd.Series(plus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    plus_di = (100.0 * (plus_dm_smooth / atr_smooth.replace(0, np.nan))).fillna(0.0)
    minus_di = (100.0 * (minus_dm_smooth / atr_smooth.replace(0, np.nan))).fillna(0.0)

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = (100.0 * (plus_di - minus_di).abs() / di_sum).fillna(0.0)
    adx = dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean().fillna(20.0)

    return adx, plus_di, minus_di


def compute_choppiness_index(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Calculate Choppiness Index (CHOP).
    Values > 61.8: Market is consolidating / choppy (Anti-trend regime)
    Values < 38.2: Market is trending strongly
    """
    prev_close = close.shift(1).fillna(close)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr1_bar = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    sum_atr = tr1_bar.rolling(window=period, min_periods=period).sum()
    max_high = high.rolling(window=period, min_periods=period).max()
    min_low = low.rolling(window=period, min_periods=period).min()
    range_hl = (max_high - min_low).replace(0, np.nan)

    ratio = (sum_atr / range_hl).clip(lower=1e-6)
    chop = 100.0 * (np.log10(ratio) / np.log10(period))
    return chop.fillna(50.0).clip(lower=0.0, upper=100.0)


def compute_mfi(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14
) -> pd.Series:
    """
    Calculate Money Flow Index (MFI).
    Volume-weighted momentum indicator measuring buying and selling pressure.
    """
    typical_price = (high + low + close) / 3.0
    raw_money_flow = typical_price * volume

    delta_tp = typical_price.diff()
    pos_flow = np.where(delta_tp > 0, raw_money_flow, 0.0)
    neg_flow = np.where(delta_tp < 0, raw_money_flow, 0.0)

    pos_sum = pd.Series(pos_flow, index=close.index).rolling(window=period, min_periods=period).sum()
    neg_sum = pd.Series(neg_flow, index=close.index).rolling(window=period, min_periods=period).sum()

    mfr = pos_sum / neg_sum.replace(0, np.nan)
    mfi = 100.0 - (100.0 / (1.0 + mfr))
    return mfi.fillna(50.0).clip(lower=0.0, upper=100.0)


def compute_chandelier_exit(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 22, multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Chandelier Exit for Long and Short trailing volatility stops.
    Long Stop: Highest High(period) - (multiplier * ATR)
    Short Stop: Lowest Low(period) + (multiplier * ATR)
    """
    atr = compute_atr(high, low, close, period=period)
    highest_high = high.rolling(window=period, min_periods=1).max()
    lowest_low = low.rolling(window=period, min_periods=1).min()

    long_stop = highest_high - (multiplier * atr)
    short_stop = lowest_low + (multiplier * atr)
    return long_stop, short_stop

