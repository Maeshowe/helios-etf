"""
Daily pipeline for HELIOS ETF FLOW.

Orchestrates the full daily calculation:
1. Fetch data from APIs (async)
2. Extract features (sync)
3. Normalize with rolling baselines
4. Calculate CAS and classify states
5. Generate explanations
6. Persist results
"""

import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from helios.core.config import Settings, get_settings
from helios.core.constants import BENCHMARK_TICKER, SECTOR_UNIVERSE
from helios.core.types import HeliosResult, SectorFeatureSet
from helios.explain.generator import ExplanationGenerator
from helios.features.aggregator import FeatureAggregator
from helios.ingest.polygon import PolygonETFClient
from helios.normalization.pipeline import NormalizationPipeline
from helios.scoring.engine import HeliosEngine

logger = logging.getLogger(__name__)


class DailyPipeline:
    """
    Daily HELIOS ETF FLOW calculation pipeline.

    This is the main entry point for daily sector allocation diagnostics.
    Orchestrates data fetching, feature extraction, normalization,
    scoring, and persistence.

    GUARDRAIL: This pipeline produces diagnostic output.
    It does NOT generate signals, alerts, or recommendations.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """
        Initialize daily pipeline.

        Args:
            settings: Application settings
            output_dir: Directory for output files
        """
        self.settings = settings or get_settings()
        self.output_dir = output_dir or self.settings.processed_data_dir / "helios"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.feature_aggregator = FeatureAggregator()
        self.normalization = NormalizationPipeline(
            history_dir=self.output_dir,
        )
        self.explanation_gen = ExplanationGenerator()
        self.engine = HeliosEngine(normalization_pipeline=self.normalization)

    async def run(
        self,
        trade_date: date | None = None,
        force_refresh: bool = False,
    ) -> HeliosResult:
        """
        Run the daily HELIOS calculation for all sectors.

        Fetches data and processes all available historical days
        to build rolling baselines, then scores the target date.

        Args:
            trade_date: Date to calculate for (default: today)
            force_refresh: Force data refresh even if cached

        Returns:
            HeliosResult with all sector allocation states
        """
        trade_date = trade_date or date.today()
        logger.info(f"Starting HELIOS ETF FLOW calculation for {trade_date}")

        # Load historical data for baselines
        self.normalization.load_history(up_to_date=trade_date)

        # Step 1: Fetch full price history (async)
        prices = await self._fetch_prices(trade_date)

        # Step 2: Process ALL historical days to build rolling baselines
        result = self._process_all_days(prices, trade_date)

        # Step 3: Persist
        self._save_result(result)

        logger.info(
            f"HELIOS for {trade_date}: "
            f"{len(result.overweight_sectors)} overweight, "
            f"{len(result.underweight_sectors)} underweight "
            f"({result.status.value})"
        )

        return result

    async def _fetch_prices(
        self,
        trade_date: date,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch full ETF price history from Polygon.

        Args:
            trade_date: End date for data fetch

        Returns:
            {ticker: DataFrame[date, open, high, low, close, volume]}
        """
        # 120 calendar days lookback for 63 trading days
        from_date = trade_date - timedelta(days=120)
        prices: dict[str, pd.DataFrame] = {}

        try:
            async with PolygonETFClient(settings=self.settings) as polygon:
                prices = await polygon.get_all_sector_prices(from_date, trade_date)
        except Exception as e:
            logger.error(f"Failed to fetch Polygon data: {e}")

        return prices

    def _process_all_days(
        self,
        prices: dict[str, pd.DataFrame],
        trade_date: date,
    ) -> HeliosResult:
        """
        Process all available historical days to build rolling baselines,
        saving every day's result to history.

        Iterates through each trading day in the price history, computing
        DollarFlow and daily returns per sector, feeding each day's features
        through the normalization rolling window.

        Args:
            prices: {ticker: DataFrame[date, open, high, low, close, volume]}
            trade_date: Target date to score

        Returns:
            HeliosResult for the target date
        """
        # Collect all unique trading dates across all tickers
        spy_df = prices.get(BENCHMARK_TICKER)
        if spy_df is None or len(spy_df) < 2:
            logger.error("No SPY data available")
            return self.engine.calculate_all(
                all_features={},
                explanation_generator=self.explanation_gen,
            )

        trading_dates = sorted(spy_df["date"].tolist())
        logger.info(f"Processing {len(trading_dates)} trading days for baseline")

        result = None
        all_rows: list[dict] = []

        # Process each day sequentially (day 0 has no prior close for returns)
        for i, day in enumerate(trading_dates):
            if i == 0:
                continue  # Need prior day for returns

            prior_day = trading_dates[i - 1]

            # SPY return for this day
            spy_today = spy_df[spy_df["date"] == day]
            spy_prior = spy_df[spy_df["date"] == prior_day]
            if spy_today.empty or spy_prior.empty:
                continue
            spy_return = float(spy_today.iloc[0]["close"]) / float(spy_prior.iloc[0]["close"]) - 1

            # Per-sector features
            sector_flows: dict[str, float | None] = {}
            sector_returns: dict[str, float | None] = {}

            for ticker in SECTOR_UNIVERSE:
                df = prices.get(ticker)
                if df is None:
                    continue

                row_today = df[df["date"] == day]
                row_prior = df[df["date"] == prior_day]

                if not row_today.empty:
                    r = row_today.iloc[0]
                    # DollarFlow = Volume * (Close - Open)
                    sector_flows[ticker] = float(r["volume"]) * (
                        float(r["close"]) - float(r["open"])
                    )

                if not row_today.empty and not row_prior.empty:
                    sector_returns[ticker] = (
                        float(row_today.iloc[0]["close"])
                        / float(row_prior.iloc[0]["close"])
                        - 1
                    )

            all_features = self.feature_aggregator.calculate_all(
                trade_date=day,
                flows=sector_flows,
                returns=sector_returns,
                spy_return=spy_return,
            )

            # Score (this feeds the rolling normalization window)
            result = self.engine.calculate_all(
                all_features=all_features,
                explanation_generator=self.explanation_gen,
            )

            # Collect rows for history
            for sector in result.sectors:
                all_rows.append({
                    "date": result.trade_date.isoformat(),
                    "ticker": sector.ticker,
                    "allocation_score": sector.allocation_score,
                    "state": sector.state.value,
                    "ap_zscore": sector.ap_zscore,
                    "rs_zscore": sector.rs_zscore,
                    "ap_raw": sector.ap_raw,
                    "rs_raw": sector.rs_raw,
                    "explanation": sector.explanation,
                    "status": sector.status.value,
                })

            if day == trade_date:
                logger.info(f"Target date {trade_date} reached — SPY return: {spy_return:.4f}")

        # Save full history
        if all_rows:
            self._save_history(all_rows)

        if result is None:
            result = self.engine.calculate_all(
                all_features={},
                explanation_generator=self.explanation_gen,
            )

        return result

    def _save_history(self, rows: list[dict]) -> None:
        """Save all collected daily rows to history parquet."""
        df = pd.DataFrame(rows)
        history_file = self.output_dir / "helios_history.parquet"
        df = df.drop_duplicates(subset=["date", "ticker"], keep="last")
        df.to_parquet(history_file, index=False)
        logger.info(
            f"Saved {len(df)} rows ({df['date'].nunique()} days) to {history_file}"
        )

    def _save_result(self, result: HeliosResult) -> None:
        """
        Save daily snapshot parquet (history is saved by _save_history).

        Args:
            result: HeliosResult to persist
        """
        rows = []
        for sector in result.sectors:
            rows.append({
                "date": result.trade_date.isoformat(),
                "ticker": sector.ticker,
                "allocation_score": sector.allocation_score,
                "state": sector.state.value,
                "ap_zscore": sector.ap_zscore,
                "rs_zscore": sector.rs_zscore,
                "ap_raw": sector.ap_raw,
                "rs_raw": sector.rs_raw,
                "status": sector.status.value,
            })

        daily_file = self.output_dir / f"{result.trade_date.isoformat()}.parquet"
        pd.DataFrame(rows).to_parquet(daily_file, index=False)

    def get_history(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        ticker: str | None = None,
    ) -> pd.DataFrame:
        """
        Load historical HELIOS results.

        Args:
            start_date: Start of date range
            end_date: End of date range
            ticker: Filter to specific sector

        Returns:
            DataFrame with historical results
        """
        history_file = self.output_dir / "helios_history.parquet"

        if not history_file.exists():
            return pd.DataFrame()

        df = pd.read_parquet(history_file)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]
        if ticker:
            df = df[df["ticker"] == ticker]

        return df.sort_values(["date", "ticker"])


def run_daily_sync(
    trade_date: date | None = None,
    force_refresh: bool = False,
) -> HeliosResult:
    """
    Synchronous wrapper for daily pipeline.

    Args:
        trade_date: Date to calculate for
        force_refresh: Force data refresh

    Returns:
        HeliosResult
    """
    pipeline = DailyPipeline()
    return asyncio.run(pipeline.run(trade_date, force_refresh))
