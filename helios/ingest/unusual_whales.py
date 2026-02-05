"""
Unusual Whales API client for ETF fund flow data.

Fetches daily ETF inflow/outflow data for sector ETFs.
Uses the /api/etfs/{ticker}/in-outflow endpoint.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from helios.core.config import Settings
from helios.core.constants import SECTOR_UNIVERSE
from helios.ingest.base import BaseAPIClient
from helios.ingest.cache import CacheManager
from helios.ingest.rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)


class UnusualWhalesClient(BaseAPIClient):
    """
    Unusual Whales API client for ETF fund flow data.

    Fetches daily net inflows/outflows (creation/redemption) for sector ETFs.
    Rate limited to 30 requests/minute (conservative).
    """

    SOURCE_NAME = "unusual_whales"
    BASE_URL = "https://api.unusualwhales.com"

    def __init__(self, settings: Settings | None = None) -> None:
        from helios.core.config import get_settings

        settings = settings or get_settings()
        super().__init__(
            api_key=settings.uw_api_key,
            base_url=self.BASE_URL,
            rate_limiter=TokenBucketLimiter.from_rpm(30, burst_size=5),
            cache=CacheManager(
                base_dir=settings.raw_data_dir / "unusual_whales",
                ttl_days=1,
            ),
        )

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _auth_params(self) -> dict[str, str]:
        return {}

    async def get_etf_inflow_outflow(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch daily inflow/outflow for an ETF.

        Args:
            ticker: ETF ticker symbol

        Returns:
            List of flow records with date, change, change_prem fields
        """
        cache_date = date.today()

        data = await self._get(
            f"/api/etfs/{ticker}/in-outflow",
            cache_key_parts=("etf_in_outflow", ticker, cache_date),
        )

        return data.get("data", [])

    async def get_all_sector_flows(
        self,
        from_date: date,
        to_date: date,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch fund flows for all sector ETFs.

        Returns:
            {ticker: DataFrame[date, net_flow]}
        """
        results: dict[str, pd.DataFrame] = {}

        for ticker in SECTOR_UNIVERSE:
            try:
                flows = await self.get_etf_inflow_outflow(ticker)
                if flows:
                    df = pd.DataFrame(flows)
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"]).dt.date
                    if "change_prem" in df.columns:
                        df["net_flow"] = pd.to_numeric(
                            df["change_prem"], errors="coerce"
                        )
                        df = df[["date", "net_flow"]].dropna(subset=["net_flow"])
                        df = df[
                            (df["date"] >= from_date) & (df["date"] <= to_date)
                        ]
                        df = df.sort_values("date").reset_index(drop=True)
                        results[ticker] = df
                        logger.debug(
                            f"Fetched {len(df)} UW flow records for {ticker}"
                        )
                    else:
                        logger.warning(
                            f"No change_prem column for {ticker}: "
                            f"{df.columns.tolist()}"
                        )
                else:
                    logger.warning(f"No UW flow data for {ticker}")
            except Exception as e:
                logger.error(f"Failed to fetch UW flows for {ticker}: {e}")

        logger.info(
            f"Fetched UW flows for {len(results)}/{len(SECTOR_UNIVERSE)} sectors"
        )
        return results

    async def health_check(self) -> bool:
        """Check Unusual Whales API connectivity."""
        try:
            data = await self._get("/api/etfs/SPY/info")
            return bool(data)
        except Exception:
            return False
