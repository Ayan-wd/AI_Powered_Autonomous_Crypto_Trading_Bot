"""
Token Bucket Rate Limiter and Network Resilience Retry Mechanism.
Prevents exchange IP rate-limit bans (Binance 429/418) and handles transient network faults.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
import random
from backend.app.core.logging import logger


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter for outbound API calls and inbound web endpoints.
    Ensures outbound calls never breach exchange limits (default: 10 requests / sec).
    """

    def __init__(self, rate_limit_per_second: float = 10.0, capacity: float = 20.0):
        self.rate = rate_limit_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
        self.total_requests_processed = 0
        self.total_throttled_events = 0

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire tokens, sleeping if necessary until capacity is available."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            # Refill tokens
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))

            if self.tokens < tokens:
                needed = tokens - self.tokens
                wait_time = needed / self.rate
                self.total_throttled_events += 1
                logger.debug(f"Rate limit reached. Throttling call for {wait_time:.3f}s...")
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.last_refill = time.monotonic()
            else:
                self.tokens -= tokens

            self.total_requests_processed += 1

    def get_status(self) -> Dict[str, Any]:
        """Return rate limiter health status."""
        return {
            "capacity": self.capacity,
            "rate_per_sec": self.rate,
            "available_tokens": round(self.tokens, 2),
            "total_requests_processed": self.total_requests_processed,
            "total_throttled_events": self.total_throttled_events,
            "is_healthy": True,
        }


async def retry_with_backoff(
    func: Callable[..., Any],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with exponential backoff and randomized jitter on failure.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                raise

            sleep_time = delay + (random.uniform(0, 0.1 * delay) if jitter else 0.0)
            logger.warning(
                f"Attempt {attempt}/{max_retries} for {func.__name__} failed with {type(e).__name__}: {e}. "
                f"Retrying in {sleep_time:.2f}s..."
            )
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor

    raise last_exception


# Global singleton rate limiter for exchange interactions
exchange_rate_limiter = TokenBucketRateLimiter(rate_limit_per_second=10.0, capacity=20.0)
