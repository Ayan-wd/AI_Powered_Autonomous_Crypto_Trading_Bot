"""
SQLAlchemy ORM models for the AI Crypto Trading Bot.
Designed for high performance with SQLite (development/paper) and PostgreSQL (production).
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Text,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class Candle(Base):
    """Normalized OHLCV market candles."""
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)
    is_closed = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_symbol_timeframe_timestamp", "symbol", "timeframe", "timestamp", unique=True),
    )


class Order(Base):
    """Order records covering paper, testnet, and live execution."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_order_id = Column(String(64), unique=True, nullable=False, index=True)
    exchange_order_id = Column(String(64), nullable=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0)
    status = Column(String(20), nullable=False, default="NEW")  # NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED
    is_paper = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Trade(Base):
    """Complete trade records with numerical reasoning and performance metrics."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(64), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY (long), SELL (short/exit)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    model_probability = Column(Float, nullable=True)
    strategy_reason = Column(String(255), nullable=True)
    explanation_json = Column(Text, nullable=True)  # Detailed numerical breakdown of feature triggers
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, CANCELED
    is_paper = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class EquitySnapshot(Base):
    """Periodic snapshots of total account equity for drawdown and performance charts."""
    __tablename__ = "equity_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    total_equity = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    drawdown_pct = Column(Float, default=0.0)
    high_water_mark = Column(Float, nullable=False)
    open_positions_count = Column(Integer, default=0)
    mode = Column(String(20), default="PAPER")


class BotLog(Base):
    """Structured audit trail of bot decisions, risk triggers, and operational events."""
    __tablename__ = "bot_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    level = Column(String(10), nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)


class ModelMetadata(Base):
    """Registry of trained ML models, validation metrics, and feature configurations."""
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(50), unique=True, nullable=False, index=True)
    algorithm = Column(String(50), default="XGBoost")
    target_horizon = Column(Integer, nullable=False)
    target_threshold = Column(Float, nullable=False)
    train_start = Column(DateTime(timezone=True), nullable=False)
    train_end = Column(DateTime(timezone=True), nullable=False)
    val_accuracy = Column(Float, nullable=True)
    val_precision = Column(Float, nullable=True)
    val_recall = Column(Float, nullable=True)
    val_f1 = Column(Float, nullable=True)
    walk_forward_metrics_json = Column(Text, nullable=True)
    feature_list_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
