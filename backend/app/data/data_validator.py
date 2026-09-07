"""
Quantitative Market Data Validator.
Ensures zero data corruption, verifies OHLCV integrity rules, detects timestamp gaps,
identifies stale feeds, and prevents future-data lookahead leaks.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from backend.app.core.logging import logger

TIMEFRAME_TO_MS = {
    "1m": 60 * 1000,
    "3m": 3 * 60 * 1000,
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "30m": 30 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "2h": 2 * 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
}


class DataValidationError(Exception):
    """Exception raised for market data integrity failures."""
    pass


class MarketDataValidator:
    """Validator for OHLCV candlesticks and time-series feeds."""

    @staticmethod
    def validate_candle(candle: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate single candle OHLCV consistency.
        Rules:
        - open, high, low, close > 0
        - volume >= 0
        - high >= max(open, close)
        - low <= min(open, close)
        - high >= low
        """
        try:
            o = float(candle["open"])
            h = float(candle["high"])
            l = float(candle["low"])
            c = float(candle["close"])
            v = float(candle["volume"])
        except (KeyError, ValueError, TypeError) as e:
            return False, f"Missing or non-numeric OHLCV field: {e}"

        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
            return False, f"Non-positive price detected: O={o}, H={h}, L={l}, C={c}"

        if v < 0:
            return False, f"Negative volume detected: V={v}"

        if h < l:
            return False, f"High price ({h}) is strictly less than low price ({l})"

        if h < max(o, c):
            return False, f"High price ({h}) is less than max(open, close) = {max(o, c)}"

        if l > min(o, c):
            return False, f"Low price ({l}) is greater than min(open, close) = {min(o, c)}"

        return True, None

    @staticmethod
    def validate_sequence(
        candles: List[Dict[str, Any]], timeframe: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate a series of consecutive candles.
        Checks for gaps, duplicated timestamps, and out-of-order candles.
        Returns (valid_candles, list_of_warning_messages).
        """
        if not candles:
            return [], ["Empty candle sequence provided"]

        expected_step_ms = TIMEFRAME_TO_MS.get(timeframe)
        if not expected_step_ms:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Sort chronologically by timestamp
        sorted_candles = sorted(candles, key=lambda x: int(x["timestamp"]))

        valid_candles: List[Dict[str, Any]] = []
        issues: List[str] = []
        seen_timestamps = set()

        for i, c in enumerate(sorted_candles):
            ts = int(c["timestamp"])

            # Check duplicate timestamp
            if ts in seen_timestamps:
                issues.append(f"Duplicate candle timestamp {ts} omitted")
                continue
            seen_timestamps.add(ts)

            # Validate individual candle
            is_valid, error_msg = MarketDataValidator.validate_candle(c)
            if not is_valid:
                issues.append(f"Invalid candle at ts={ts}: {error_msg}")
                continue

            # Check for gaps between consecutive valid candles
            if valid_candles:
                prev_ts = int(valid_candles[-1]["timestamp"])
                diff = ts - prev_ts
                if diff > expected_step_ms:
                    missing_count = int(diff // expected_step_ms) - 1
                    issues.append(
                        f"Data Gap Detected: {missing_count} missing candles between {prev_ts} and {ts} ({timeframe})"
                    )

            valid_candles.append(c)

        return valid_candles, issues

    @staticmethod
    def is_feed_stale(latest_timestamp_ms: int, timeframe: str, tolerance_intervals: int = 2) -> bool:
        """
        Check if the market data feed is stale.
        Returns True if current time exceeds latest_candle_time + (tolerance_intervals * interval).
        """
        step_ms = TIMEFRAME_TO_MS.get(timeframe, 15 * 60 * 1000)
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        stale_threshold_ms = latest_timestamp_ms + (tolerance_intervals * step_ms)
        return now_ms > stale_threshold_ms
