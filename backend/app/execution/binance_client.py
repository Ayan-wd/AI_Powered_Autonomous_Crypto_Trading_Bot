"""
Binance Spot exchange adapter supporting both Spot Testnet and Live (when authorized).
Provides authenticated HMAC-SHA256 request signing for trading and public endpoints for market data.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.execution.exchange_interface import ExchangeInterface, OrderBookData, TickerData


_DEFAULT = object()


class BinanceClient(ExchangeInterface):
    """Async Binance Spot API Client."""

    def __init__(
        self,
        api_key: Any = _DEFAULT,
        api_secret: Any = _DEFAULT,
        testnet: Optional[bool] = None,
    ):
        self.api_key = settings.BINANCE_API_KEY if api_key is _DEFAULT else api_key
        self.api_secret = settings.BINANCE_API_SECRET if api_secret is _DEFAULT else api_secret
        self.testnet = testnet if testnet is not None else settings.BINANCE_TESTNET

        if self.testnet:
            self.base_url = "https://testnet.binance.vision/api/v3"
        else:
            self.base_url = "https://api.binance.com/api/v3"

        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize the underlying HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {},
            )
            logger.info(f"Binance client initialized. Testnet={self.testnet}, BaseURL={self.base_url}")

    async def close(self) -> None:
        """Close HTTP client session."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("Binance client connection closed.")

    def _generate_signature(self, query_string: str) -> str:
        """Compute HMAC SHA256 signature for private endpoints."""
        if not self.api_secret:
            raise ValueError("BINANCE_API_SECRET is required to sign private API requests.")
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """Execute HTTP request with error handling and signing."""
        if self._client is None or self._client.is_closed:
            await self.initialize()

        params = params or {}
        headers = {}

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("Binance API key and secret are required for signed operations.")
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 60000
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            signature = self._generate_signature(query_string)
            url = f"{url}?{query_string}&signature={signature}"
            params = None
            headers["X-MBX-APIKEY"] = self.api_key

        try:
            response = await self._client.request(method, url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Binance HTTP error {e.response.status_code} on {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Binance connection error on {endpoint}: {e}")
            raise

    async def get_ticker(self, symbol: str) -> TickerData:
        """Fetch 24h ticker price statistics."""
        data = await self._request("GET", "ticker/24hr", params={"symbol": symbol})
        return TickerData(
            symbol=symbol,
            price=float(data["lastPrice"]),
            bid_price=float(data.get("bidPrice", data["lastPrice"])),
            ask_price=float(data.get("askPrice", data["lastPrice"])),
            volume_24h=float(data["volume"]),
            price_change_24h_pct=float(data["priceChangePercent"]),
            timestamp=int(data["closeTime"]),
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch OHLCV candlestick data."""
        params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        raw_klines = await self._request("GET", "klines", params=params)

        formatted = []
        for k in raw_klines:
            formatted.append({
                "timestamp": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": int(k[6]),
                "quote_volume": float(k[7]),
                "trades_count": int(k[8]),
                "is_closed": True,
            })
        return formatted

    async def get_order_book(self, symbol: str, limit: int = 20) -> OrderBookData:
        """Fetch market depth."""
        data = await self._request("GET", "depth", params={"symbol": symbol, "limit": limit})
        return OrderBookData(
            symbol=symbol,
            bids=[[float(p), float(q)] for p, q in data.get("bids", [])],
            asks=[[float(p), float(q)] for p, q in data.get("asks", [])],
            timestamp=int(time.time() * 1000),
        )

    async def ping(self) -> bool:
        """Test connectivity to Binance API."""
        try:
            await self._request("GET", "ping")
            return True
        except Exception as e:
            logger.warning(f"Binance ping failed: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Fetch system status and server time."""
        try:
            server_time_res = await self._request("GET", "time")
            server_time = server_time_res.get("serverTime")
            return {
                "status": "ONLINE",
                "testnet": self.testnet,
                "base_url": self.base_url,
                "server_time": server_time,
                "latency_ms": int(time.time() * 1000) - int(server_time) if server_time else 0,
            }
        except Exception as e:
            return {
                "status": "OFFLINE",
                "testnet": self.testnet,
                "base_url": self.base_url,
                "error": str(e),
            }

    async def get_account_info(self) -> Dict[str, Any]:
        """Fetch raw account details with security permission verification (Signed)."""
        data = await self._request("GET", "account", signed=True)
        return {
            "maker_commission": data.get("makerCommission", 0),
            "taker_commission": data.get("takerCommission", 0),
            "can_trade": data.get("canTrade", False),
            "can_withdraw": data.get("canWithdraw", False),  # Must be False for bot API keys!
            "can_deposit": data.get("canDeposit", False),
            "account_type": data.get("accountType", "SPOT"),
            "balances": {
                b["asset"]: float(b["free"]) + float(b["locked"])
                for b in data.get("balances", [])
                if float(b["free"]) + float(b["locked"]) > 0.0
            },
        }

    async def get_account_balance(self) -> Dict[str, float]:
        """Fetch account balances (Signed)."""
        data = await self._request("GET", "account", signed=True)
        balances = {}
        for b in data.get("balances", []):
            free = float(b["free"])
            locked = float(b["locked"])
            total = free + locked
            if total > 0.0:
                balances[b["asset"]] = total
        return balances

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch open orders (Signed)."""
        params = {"symbol": symbol} if symbol else {}
        return await self._request("GET", "openOrders", params=params, signed=True)

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an order (Signed)."""
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": f"{quantity:.6f}",
        }
        if price:
            params["price"] = f"{price:.2f}"
            params["timeInForce"] = "GTC"
        if stop_price:
            params["stopPrice"] = f"{stop_price:.2f}"
        if client_order_id:
            params["newClientOrderId"] = client_order_id

        return await self._request("POST", "order", params=params, signed=True)

    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order (Signed)."""
        params = {"symbol": symbol, "orderId": order_id}
        return await self._request("DELETE", "order", params=params, signed=True)

    async def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Query order status (Signed)."""
        params = {"symbol": symbol, "orderId": order_id}
        return await self._request("GET", "order", params=params, signed=True)
