"""
FMP API client for ETF fund flow data.

Fetches daily net fund flow data for sector ETFs.
Requires FMP Ultimate tier for /stable/etf-fund-flow endpoint.
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


class FMPFlowClient(BaseAPIClient):
    """
    FMP Ultimate API client for ETF fund flow data.

    Fetches daily net inflows/outflows for sector ETFs.
    Rate limited to 10 requests/minute (conservative for free tier).
    """

    SOURCE_NAME = "fmp"
    BASE_URL = "https://financialmodelingprep.com"

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize FMP client.

        Args:
            settings: Application settings (uses default if not provided)
        """
        from helios.core.config import get_settings

        settings = settings or get_settings()
        super().__init__(
            api_key=settings.fmp_key,
            base_url=self.BASE_URL,
            rate_limiter=TokenBucketLimiter.from_rpm(10, burst_size=5),
            cache=CacheManager(
                base_dir=settings.raw_data_dir / "fmp",
                ttl_days=7,
            ),
        )

    def _auth_headers(self) -> dict[str, str]:
        return {}

    def _auth_params(self) -> dict[str, str]:
        return {"apikey": self.api_key}

    async def get_etf_fund_flow(
        self,
        ticker: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch daily net fund flow for an ETF.

        Args:
            ticker: ETF ticker symbol
            from_date: Start date (optional)
            to_date: End date (optional)

        Returns:
            List of flow records with date and netFlow fields
        """
        params: dict[str, Any] = {"symbol": ticker}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        cache_date = to_date or date.today()

        data = await self._get(
            "/stable/etf-fund-flow",
            params=params,
            cache_key_parts=("etf_fund_flow", ticker, cache_date),
        )

        # FMP returns list directly or wrapped in a dict
        if isinstance(data, list):
            return data
        return data.get("results", data.get("data", []))

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
                flows = await self.get_etf_fund_flow(ticker, from_date, to_date)
                if flows:
                    df = pd.DataFrame(flows)
                    # Normalize column names
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"]).dt.date
                    # Look for net flow column (various possible names)
                    flow_col = None
                    for col in ["netFlow", "net_flow", "flowAmount", "flow"]:
                        if col in df.columns:
                            flow_col = col
                            break

                    if flow_col:
                        df = df.rename(columns={flow_col: "net_flow"})
                        df = df[["date", "net_flow"]].sort_values("date").reset_index(drop=True)
                        results[ticker] = df
                        logger.debug(f"Fetched {len(df)} flow records for {ticker}")
                    else:
                        logger.warning(f"No net flow column found for {ticker}: {df.columns.tolist()}")
                else:
                    logger.warning(f"No flow data for {ticker}")
            except Exception as e:
                logger.error(f"Failed to fetch flows for {ticker}: {e}")

        logger.info(f"Fetched flows for {len(results)}/{len(SECTOR_UNIVERSE)} sectors")
        return results

    async def health_check(self) -> bool:
        """Check FMP API connectivity."""
        try:
            data = await self._get(
                "/stable/etf-info",
                params={"symbol": "SPY"},
            )
            return bool(data)
        except Exception:
            return False
