"""
Rolling statistics calculator for HELIOS ETF FLOW.

Maintains rolling window statistics for baseline normalization.
Sector-aware: each (sector, feature) pair gets independent statistics.
"""

import logging
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from helios.core.constants import FEATURE_NAMES, MIN_OBSERVATIONS, ROLLING_WINDOW, SECTOR_UNIVERSE

logger = logging.getLogger(__name__)


@dataclass
class RollingStats:
    """
    Rolling statistics for a single feature.

    Maintains a fixed-size window of historical values
    and computes mean/std for z-score normalization.
    """

    feature_name: str
    window: int = ROLLING_WINDOW
    min_observations: int = MIN_OBSERVATIONS
    _values: deque = field(default_factory=lambda: deque(maxlen=63))
    _dates: deque = field(default_factory=lambda: deque(maxlen=63))

    def __post_init__(self) -> None:
        """Initialize deques with correct maxlen."""
        self._values = deque(maxlen=self.window)
        self._dates = deque(maxlen=self.window)

    def add(self, value: float, trade_date: date) -> None:
        """
        Add a new observation.

        Args:
            value: Feature value to add
            trade_date: Date of observation
        """
        self._values.append(value)
        self._dates.append(trade_date)

    def add_bulk(self, values: Sequence[float], dates: Sequence[date]) -> None:
        """
        Add multiple observations at once.

        Args:
            values: Sequence of values (oldest to newest)
            dates: Corresponding dates
        """
        for v, d in zip(values, dates, strict=True):
            self.add(v, d)

    @property
    def count(self) -> int:
        """Number of observations in window."""
        return len(self._values)

    @property
    def is_ready(self) -> bool:
        """Whether we have enough observations for valid statistics."""
        return self.count >= self.min_observations

    @property
    def mean(self) -> float | None:
        """Rolling mean, or None if insufficient data."""
        if not self.is_ready:
            return None
        return float(np.mean(list(self._values)))

    @property
    def std(self) -> float | None:
        """Rolling std (sample), or None if insufficient data."""
        if not self.is_ready:
            return None
        return float(np.std(list(self._values), ddof=1))

    @property
    def values(self) -> list[float]:
        """List of values in window."""
        return list(self._values)

    @property
    def dates(self) -> list[date]:
        """List of dates in window."""
        return list(self._dates)

    def clear(self) -> None:
        """Clear all observations."""
        self._values.clear()
        self._dates.clear()


class SectorRollingCalculator:
    """
    Manages rolling statistics for all features across all sectors.

    Structure: {ticker: {feature_name: RollingStats}}

    Each (sector, feature) pair gets its own independent rolling window.
    With 11 sectors and 2 features, this maintains 22 windows.
    """

    def __init__(
        self,
        tickers: Sequence[str] = SECTOR_UNIVERSE,
        feature_names: Sequence[str] = FEATURE_NAMES,
        window: int = ROLLING_WINDOW,
        min_observations: int = MIN_OBSERVATIONS,
    ) -> None:
        """
        Initialize calculator for all (sector, feature) pairs.

        Args:
            tickers: List of sector ETF tickers
            feature_names: List of feature names to track
            window: Rolling window size
            min_observations: Minimum observations required
        """
        self.window = window
        self.min_observations = min_observations
        self._stats: dict[str, dict[str, RollingStats]] = {
            ticker: {
                feature: RollingStats(
                    feature_name=feature,
                    window=window,
                    min_observations=min_observations,
                )
                for feature in feature_names
            }
            for ticker in tickers
        }

    def add_observation(
        self,
        ticker: str,
        trade_date: date,
        features: dict[str, float],
    ) -> None:
        """
        Add observation for a sector's features.

        Args:
            ticker: Sector ETF ticker
            trade_date: Date of observation
            features: Dict of feature name -> value
        """
        if ticker not in self._stats:
            return

        for name, value in features.items():
            if name in self._stats[ticker] and value is not None:
                self._stats[ticker][name].add(value, trade_date)

    def get_stats(self, ticker: str, feature_name: str) -> RollingStats | None:
        """
        Get rolling stats for a (sector, feature) pair.

        Args:
            ticker: Sector ETF ticker
            feature_name: Name of feature

        Returns:
            RollingStats or None if not tracked
        """
        return self._stats.get(ticker, {}).get(feature_name)

    def get_zscore(self, ticker: str, feature_name: str, value: float) -> float | None:
        """
        Calculate z-score for a (sector, feature) value.

        IMPORTANT: Z-scores are NOT clipped.

        Args:
            ticker: Sector ETF ticker
            feature_name: Name of feature
            value: Current value

        Returns:
            Z-score or None if insufficient history
        """
        stats = self.get_stats(ticker, feature_name)
        if stats is None or not stats.is_ready:
            return None

        mean = stats.mean
        std = stats.std

        if mean is None or std is None or std == 0:
            return None

        # NO CLIPPING - preserve tail information
        return (value - mean) / std

    def get_ready_features(self, ticker: str) -> list[str]:
        """Get list of features with sufficient history for a sector."""
        if ticker not in self._stats:
            return []
        return [name for name, stats in self._stats[ticker].items() if stats.is_ready]

    def get_not_ready_features(self, ticker: str) -> list[str]:
        """Get list of features without sufficient history for a sector."""
        if ticker not in self._stats:
            return []
        return [name for name, stats in self._stats[ticker].items() if not stats.is_ready]

    def summary(self) -> dict[str, dict[str, dict]]:
        """
        Get summary of all rolling statistics.

        Returns:
            {ticker: {feature: {count, is_ready, mean, std}}}
        """
        return {
            ticker: {
                name: {
                    "count": stats.count,
                    "is_ready": stats.is_ready,
                    "mean": stats.mean,
                    "std": stats.std,
                }
                for name, stats in features.items()
            }
            for ticker, features in self._stats.items()
        }

    def load_from_history(
        self,
        history: dict[str, list[dict]],
        date_key: str = "date",
    ) -> int:
        """
        Load historical data into rolling stats.

        Args:
            history: {ticker: [records]} with date and feature values
            date_key: Key for date field in records

        Returns:
            Number of observations loaded
        """
        count = 0
        for ticker, records in history.items():
            if ticker not in self._stats:
                continue

            for record in records:
                trade_date = record.get(date_key)
                if trade_date is None:
                    continue

                # Convert string date if needed
                if isinstance(trade_date, str):
                    trade_date = date.fromisoformat(trade_date)

                features = {k: v for k, v in record.items() if k != date_key and v is not None}
                self.add_observation(ticker, trade_date, features)
                count += 1

        logger.info(f"Loaded {count} historical observations across sectors")
        return count
