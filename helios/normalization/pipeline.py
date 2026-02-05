"""
Multi-sector normalization pipeline for HELIOS ETF FLOW.

Orchestrates rolling z-score normalization across all sectors.

CRITICAL DESIGN DECISIONS:
1. Z-scores are NOT clipped at feature level
2. Features with n < N_min are excluded, not imputed
3. Each sector has independent rolling baselines
4. NO percentile ranking for state classification
   (CAS thresholds operate directly in z-score space)
"""

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from helios.core.constants import (
    FEATURE_NAMES,
    MIN_OBSERVATIONS,
    ROLLING_WINDOW,
    SECTOR_UNIVERSE,
)
from helios.core.types import BaselineStatus, SectorFeatureSet
from helios.normalization.rolling import SectorRollingCalculator

logger = logging.getLogger(__name__)


class NormalizationPipeline:
    """
    Sector-aware normalization pipeline.

    Manages rolling baselines and computes z-scores for all
    (sector, feature) pairs independently.
    """

    def __init__(
        self,
        window: int = ROLLING_WINDOW,
        min_observations: int = MIN_OBSERVATIONS,
        history_dir: Path | None = None,
    ) -> None:
        """
        Initialize normalization pipeline.

        Args:
            window: Rolling window size (default 63)
            min_observations: Minimum observations (default 21)
            history_dir: Directory containing historical parquet files
        """
        self._calculator = SectorRollingCalculator(
            tickers=SECTOR_UNIVERSE,
            feature_names=FEATURE_NAMES,
            window=window,
            min_observations=min_observations,
        )
        self._history_dir = history_dir

    def load_history(self, up_to_date: date | None = None) -> int:
        """
        Load historical data for baseline initialization.

        Args:
            up_to_date: Only load history up to this date

        Returns:
            Number of observations loaded
        """
        if self._history_dir is None:
            logger.debug("No history directory configured")
            return 0

        history_file = self._history_dir / "helios_history.parquet"
        if not history_file.exists():
            logger.info("No history file found, starting fresh")
            return 0

        try:
            df = pd.read_parquet(history_file)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            if up_to_date:
                df = df[df["date"] < up_to_date]

            # Convert DataFrame to {ticker: [records]} format
            history: dict[str, list[dict]] = {}
            for ticker in SECTOR_UNIVERSE:
                ticker_df = df[df["ticker"] == ticker]
                if not ticker_df.empty:
                    records = []
                    for _, row in ticker_df.iterrows():
                        record: dict = {"date": row["date"]}
                        if pd.notna(row.get("ap_raw")):
                            record["AP"] = float(row["ap_raw"])
                        if pd.notna(row.get("rs_raw")):
                            record["RS"] = float(row["rs_raw"])
                        records.append(record)
                    history[ticker] = records

            count = self._calculator.load_from_history(history)
            logger.info(f"Loaded {count} historical observations for baselines")
            return count

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return 0

    def normalize_sector(
        self,
        ticker: str,
        features: SectorFeatureSet,
    ) -> tuple[dict[str, float], list[str], BaselineStatus]:
        """
        Normalize features for a single sector.

        Args:
            ticker: Sector ETF ticker
            features: Raw feature values

        Returns:
            Tuple of (z_scores, excluded_features, status)
        """
        z_scores: dict[str, float] = {}
        excluded: list[str] = []

        # Map SectorFeatureSet fields to feature values
        feature_values: dict[str, float | None] = {
            "AP": features.net_flow,
            "RS": features.excess_return,
        }

        for feature_name, raw_value in feature_values.items():
            if raw_value is None:
                excluded.append(feature_name)
                continue

            z = self._calculator.get_zscore(ticker, feature_name, raw_value)
            if z is None:
                excluded.append(feature_name)
            else:
                z_scores[feature_name] = z

        # Determine status
        if len(z_scores) == len(FEATURE_NAMES):
            status = BaselineStatus.COMPLETE
        elif len(z_scores) > 0:
            status = BaselineStatus.PARTIAL
        else:
            status = BaselineStatus.INSUFFICIENT

        return z_scores, excluded, status

    def normalize_all(
        self,
        all_features: dict[str, SectorFeatureSet],
    ) -> dict[str, tuple[dict[str, float], list[str], BaselineStatus]]:
        """
        Normalize features for all sectors.

        Args:
            all_features: {ticker: SectorFeatureSet}

        Returns:
            {ticker: (z_scores, excluded, status)}
        """
        results: dict[str, tuple[dict[str, float], list[str], BaselineStatus]] = {}

        for ticker, features in all_features.items():
            results[ticker] = self.normalize_sector(ticker, features)

        return results

    def add_observation(self, ticker: str, features: SectorFeatureSet) -> None:
        """
        Add observation to rolling baselines.

        Args:
            ticker: Sector ETF ticker
            features: Feature values to add
        """
        feature_values: dict[str, float] = {}
        if features.net_flow is not None:
            feature_values["AP"] = features.net_flow
        if features.excess_return is not None:
            feature_values["RS"] = features.excess_return

        if feature_values:
            self._calculator.add_observation(
                ticker, features.trade_date, feature_values
            )

    def summary(self) -> dict:
        """Get summary of all rolling statistics."""
        return self._calculator.summary()
