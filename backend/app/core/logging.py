"""
Structured logging configuration module using loguru.
Supports structured JSON logging for monitoring, colored console output for development,
and automatic sanitization of sensitive credentials.
"""

import sys
from pathlib import Path
from loguru import logger
from backend.app.core.config import settings

# Create logs directory if it does not exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_message(record: dict) -> bool:
    """Mask any accidentally leaked API keys or secrets in logs."""
    msg = record["message"]
    if settings.BINANCE_API_SECRET and settings.BINANCE_API_SECRET in msg:
        record["message"] = msg.replace(settings.BINANCE_API_SECRET, "***REDACTED_SECRET***")
    if settings.BINANCE_API_KEY and len(settings.BINANCE_API_KEY) > 8 and settings.BINANCE_API_KEY in msg:
        record["message"] = msg.replace(settings.BINANCE_API_KEY, "***MASKED_KEY***")
    return True


def setup_logging():
    """Configure system-wide loguru logging."""
    logger.remove()

    # 1. Console Output - Human-friendly colored format
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter=sanitize_message,
        colorize=True,
    )

    # 2. Main System Log File (Rotating daily / 10MB)
    logger.add(
        LOGS_DIR / "trading_bot.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        filter=sanitize_message,
        encoding="utf-8",
    )

    # 3. Trade Audit Log (JSON format for structured analysis)
    logger.add(
        LOGS_DIR / "trades_audit.json",
        level="INFO",
        format="{message}",
        filter=lambda record: "trade_event" in record["extra"],
        rotation="50 MB",
        retention="30 days",
        serialize=True,
        encoding="utf-8",
    )

    # 4. Risk Alert Log
    logger.add(
        LOGS_DIR / "risk_events.log",
        level="WARNING",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | RISK: {message}",
        filter=lambda record: "risk_event" in record["extra"],
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )

    logger.info(f"Logging initialized. Mode: {settings.TRADING_MODE.value}, Log Level: {settings.LOG_LEVEL}")


# Export logger instance
__all__ = ["logger", "setup_logging"]
