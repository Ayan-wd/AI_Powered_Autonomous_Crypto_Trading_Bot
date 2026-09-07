"""
Technical indicator and feature inspection endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import get_db
from backend.app.features.feature_engineering import FeaturePipeline

router = APIRouter(prefix="/features", tags=["Features"])
market_engine = MarketDataEngine()


@router.get("/latest")
async def get_latest_indicators(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the latest real-time technical indicators computed on candles."""
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=250, session=db
        )
        if df.empty or len(df) < 50:
            return {
                "status": "INSUFFICIENT_DATA",
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "candle_count": len(df),
                "message": "Need at least 50 candles to compute 200 EMA and multi-period features.",
            }

        df_features = FeaturePipeline.build_features(df, drop_na=False)
        latest = df_features.iloc[-1]

        trend_str = "BULLISH" if latest.get("regime_trend") == 1 else ("BEARISH" if latest.get("regime_trend") == -1 else "RANGING")
        vol_str = "HIGH" if latest.get("regime_volatility") == 1 else ("LOW" if latest.get("regime_volatility") == -1 else "NORMAL")

        return {
            "status": "OK",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": str(latest.name),
            "price": float(latest["close"]),
            "rsi_14": round(float(latest.get("rsi_14", 50.0)), 2),
            "macd": {
                "value": round(float(latest.get("macd_norm", 0.0) * latest["close"]), 2),
                "signal": round(float(latest.get("macd_signal_norm", 0.0) * latest["close"]), 2),
                "hist": round(float(latest.get("macd_hist_norm", 0.0) * latest["close"]), 2),
            },
            "ema": {
                "ema20": round(float(latest.get("ema_20", latest["close"])), 2),
                "ema50": round(float(latest.get("ema_50", latest["close"])), 2),
                "ema200": round(float(latest.get("ema_200", latest["close"])), 2),
            },
            "bollinger": {
                "upper": round(float(latest.get("bb_upper", latest["close"])), 2),
                "middle": round(float(latest.get("bb_middle", latest["close"])), 2),
                "lower": round(float(latest.get("bb_lower", latest["close"])), 2),
                "width": round(float(latest.get("bb_width", 0.0)), 4),
            },
            "atr_14": round(float(latest.get("atr_14", 0.0)), 2),
            "returns": {
                "return_1p": round(float(latest.get("return_1p", 0.0)), 4),
                "return_3p": round(float(latest.get("return_3p", 0.0)), 4),
                "return_5p": round(float(latest.get("return_5p", 0.0)), 4),
            },
            "regimes": {
                "trend": trend_str,
                "volatility": vol_str,
            },
        }
    except Exception as e:
        logger.error(f"Error computing indicators: {e}")
        return {"status": "ERROR", "message": str(e)}
