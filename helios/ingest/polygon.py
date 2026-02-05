"""
Polygon.io API client for ETF daily prices.

Fetches daily OHLCV data for sector ETFs and SPY benchmark.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from helios.core.config import Settings
from helios.core.constants import BENCHMARK_TICKER, SECTOR_UNIVERSE
from helios.ingest.base import BaseAPIClient
from helios.ingest.cache import CacheManager
from helios.ingest.rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)


class PolygonETFClient(BaseAPIClient):
    """
    Polygon.io client for ETF daily prices.

    Fetches daily OHLCV bars for sector ETFs and SPY.
    Rate limited to 5 requests/minute (free tier).
    """

    SOURCE_NAME = "polygon"
    BASE_URL = "https://api.polygon.io"

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize Polygon client.

        Args:
            settings: Application settings (uses default if not provided)
        """
        from helios.core.config import get_settings

        settings = settings or get_settings()
        super().__init__(
            api_key=settings.polygon_key,
            base_url=self.BASE_URL,
            rate_limiter=TokenBucketLimiter.from_rpm(5, burst_size=5),
            cache=CacheManager(
                base_dir=settings.raw_data_dir / "polygon",
                ttl_days=7,
            ),
        )

    def _auth_headers(self) -> dict[str, str]:
        return {}

    def _auth_params(self) -> dict[str, str]:
        return {"apiKey": self.api_key}

    async def get_etf_daily(
        self,
        ticker: str,
        from_date: date,
        to_date: date,
    ) -> list[dict[str, Any]]:
        """
        Fetch daily OHLCV bars for a single ETF.

        Args:
            ticker: ETF ticker symbol
            from_date: Start date
            to_date: End date

        Returns:
            List of daily bar dicts with o, h, l, c, v, t fields
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date.isoformat()}/{to_date.isoformat()}"

        data = await self._get(
            endpoint,
            params={"adjusted": "true", "sort": "asc", "limit": "250"},
            cache_key_parts=("ticker_aggs", ticker, to_date),
        )

        return data.get("results", [])

    async def get_all_sector_prices(
        self,
        from_date: date,
        to_date: date,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch daily prices for all sector ETFs + SPY.

        Returns:
            {ticker: DataFrame[date, open, high, low, close, volume]}
        """
        all_tickers = list(SECTOR_UNIVERSE) + [BENCHMARK_TICKER]
        results: dict[str, pd.DataFrame] = {}

        for ticker in all_tickers:
            try:
                bars = await self.get_etf_daily(ticker, from_date, to_date)
                if bars:
                    df = pd.DataFrame(bars)
                    # Polygon uses 't' for timestamp (ms), 'o','h','l','c','v' for OHLCV
                    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.date
                    df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
                    df = df[["date", "open", "high", "low", "close", "volume"]]
                    df = df.sort_values("date").reset_index(drop=True)
                    results[ticker] = df
                    logger.debug(f"Fetched {len(df)} bars for {ticker}")
                else:
                    logger.warning(f"No price data for {ticker}")
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")

        logger.info(f"Fetched prices for {len(results)}/{len(all_tickers)} tickers")
        return results

    @staticmethod
    def calculate_returns(prices_df: pd.DataFrame) -> pd.Series:
        """
        Calculate daily returns from close prices.

        Args:
            prices_df: DataFrame with 'close' column

        Returns:
            Series of daily returns
        """
        return prices_df["close"].pct_change()

    async def health_check(self) -> bool:
        """Check Polygon API connectivity."""
        try:
            data = await self._get("/v1/marketstatus/now")
            return "market" in data
        except Exception:
            return False
