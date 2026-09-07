"""
Core configuration module for the AI Crypto Trading Bot.
Enforces strict security validation, safe defaults (PAPER mode by default),
and failsafe dual-confirmation for live trading.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(str, Enum):
    PAPER = "PAPER"
    TESTNET = "TESTNET"
    LIVE = "LIVE"


class BotState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Project Metadata ---
    PROJECT_NAME: str = "AI Autonomous Crypto Trading Bot"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # --- Exchange Settings ---
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True

    # --- Operational Mode & Safeguards ---
    # Default is PAPER trading (virtual simulation with zero financial risk)
    TRADING_MODE: TradingMode = TradingMode.PAPER
    # Global toggle - even in PAPER/TESTNET, orders won't place unless enabled
    TRADING_ENABLED: bool = False
    # CRITICAL: Dual-confirmation flag required for any live funds
    LIVE_TRADING: bool = False

    # --- Capital & Trading Parameters ---
    STARTING_CAPITAL: float = Field(default=50.0, gt=0, description="Virtual or initial capital in USD")
    BASE_CURRENCY: str = "USDT"
    TRADING_SYMBOL: str = "BTCUSDT"
    DEFAULT_TIMEFRAME: str = "15m"

    # --- Database Configuration ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/trading_bot.db"

    # --- Machine Learning Engine Settings ---
    MODEL_PATH: str = "./models/xgboost_btc_15m.json"
    FEATURE_SCALER_PATH: str = "./models/scaler_btc_15m.joblib"
    MIN_PREDICTION_CONFIDENCE: float = Field(default=0.65, ge=0.5, le=1.0)
    PREDICTION_HORIZON_CANDLES: int = Field(default=4, ge=1)
    TARGET_RETURN_THRESHOLD: float = Field(default=0.005, gt=0.0)

    # --- Risk Management Controls ---
    MAX_RISK_PER_TRADE_PCT: float = Field(default=0.01, ge=0.001, le=0.05, description="Max 1% risk per trade")
    MAX_POSITION_SIZE_USD: float = Field(default=10.0, gt=0, description="Max $10 position on $50 account")
    MAX_DAILY_LOSS_PCT: float = Field(default=0.03, ge=0.01, le=0.10, description="Stop if daily loss >= 3%")
    MAX_WEEKLY_LOSS_PCT: float = Field(default=0.08, ge=0.02, le=0.20, description="Stop if weekly loss >= 8%")
    MAX_DRAWDOWN_PCT: float = Field(default=0.10, ge=0.05, le=0.30, description="Kill switch if drawdown >= 10%")
    MAX_CONSECUTIVE_LOSSES: int = Field(default=3, ge=1, le=10)
    MAX_DAILY_TRADES: int = Field(default=10, ge=1, le=50)
    DEFAULT_STOP_LOSS_PCT: float = Field(default=0.015, gt=0.0, le=0.10)
    DEFAULT_TAKE_PROFIT_PCT: float = Field(default=0.030, gt=0.0, le=0.20)

    # --- Server & Monitoring ---
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @model_validator(mode="after")
    def validate_safety_invariants(self) -> "Settings":
        """Strict validation of trading safety invariants."""
        # 1. Refuse LIVE mode unless LIVE_TRADING is explicitly true
        if self.TRADING_MODE == TradingMode.LIVE and not self.LIVE_TRADING:
            raise ValueError(
                "CRITICAL SAFETY VIOLATION: Cannot set TRADING_MODE='LIVE' unless LIVE_TRADING=True "
                "is explicitly configured in environment variables."
            )

        # 2. In TESTNET or LIVE mode, API keys must be provided when TRADING_ENABLED=True
        if self.TRADING_MODE in (TradingMode.TESTNET, TradingMode.LIVE) and self.TRADING_ENABLED:
            if not self.BINANCE_API_KEY or not self.BINANCE_API_SECRET:
                raise ValueError(
                    f"Exchange API credentials (BINANCE_API_KEY, BINANCE_API_SECRET) are required "
                    f"when TRADING_ENABLED=True in {self.TRADING_MODE.value} mode."
                )

        # 3. Guard position size against starting capital
        if self.MAX_POSITION_SIZE_USD > self.STARTING_CAPITAL:
            raise ValueError(
                f"MAX_POSITION_SIZE_USD ({self.MAX_POSITION_SIZE_USD}) cannot exceed STARTING_CAPITAL ({self.STARTING_CAPITAL})"
            )

        return self

    def sanitized_dict(self) -> dict:
        """Returns configuration dictionary with secrets masked for safe client delivery."""
        data = self.model_dump()
        if data.get("BINANCE_API_KEY"):
            data["BINANCE_API_KEY"] = (
                data["BINANCE_API_KEY"][:4] + "..." + data["BINANCE_API_KEY"][-4:]
                if len(data["BINANCE_API_KEY"]) > 8
                else "***MASKED***"
            )
        if data.get("BINANCE_API_SECRET"):
            data["BINANCE_API_SECRET"] = "***REDACTED***"
        return data


# Global cached settings instance
settings = Settings()
