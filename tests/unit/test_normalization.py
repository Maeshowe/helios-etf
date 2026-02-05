"""
Tests for normalization module.

CRITICAL: Verifies NO CLIPPING behavior at the z-score level.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from helios.core.types import BaselineStatus, SectorFeatureSet
from helios.normalization.methods import percentile_rank, zscore_normalize
from helios.normalization.rolling import RollingStats, SectorRollingCalculator


class TestZScoreNormalize:
    """Test z-score normalization."""

    def test_basic_zscore(self) -> None:
        """Standard z-score calculation."""
        z = zscore_normalize(110.0, mean=100.0, std=10.0)
        assert z == pytest.approx(1.0)

    def test_negative_zscore(self) -> None:
        """Negative z-score for below-mean value."""
        z = zscore_normalize(80.0, mean=100.0, std=10.0)
        assert z == pytest.approx(-2.0)

    def test_no_clipping_positive(self) -> None:
        """CRITICAL: Z-scores above +3 are NOT clipped."""
        z = zscore_normalize(150.0, mean=100.0, std=10.0)
        assert z == pytest.approx(5.0)  # NOT clipped to 3.0

    def test_no_clipping_negative(self) -> None:
        """CRITICAL: Z-scores below -3 are NOT clipped."""
        z = zscore_normalize(50.0, mean=100.0, std=10.0)
        assert z == pytest.approx(-5.0)  # NOT clipped to -3.0

    def test_extreme_zscore_preserved(self) -> None:
        """Extreme z-scores (+7) must be preserved for tail information."""
        z = zscore_normalize(170.0, mean=100.0, std=10.0)
        assert z == pytest.approx(7.0)  # Tail preserved

    def test_zero_std_returns_zero(self) -> None:
        """Zero standard deviation returns 0.0."""
        z = zscore_normalize(100.0, mean=100.0, std=0.0)
        assert z == 0.0

    def test_nan_std_returns_zero(self) -> None:
        """NaN standard deviation returns 0.0."""
        z = zscore_normalize(100.0, mean=100.0, std=float("nan"))
        assert z == 0.0


class TestPercentileRank:
    """Test percentile ranking (for dashboard display only)."""

    def test_basic_percentile(self) -> None:
        """Value above all history gets 100%."""
        p = percentile_rank(10.0, [1.0, 2.0, 3.0, 4.0, 5.0])
        assert p == pytest.approx(100.0)

    def test_below_all_percentile(self) -> None:
        """Value below all history gets 0%."""
        p = percentile_rank(0.0, [1.0, 2.0, 3.0, 4.0, 5.0])
        assert p == pytest.approx(0.0)

    def test_middle_percentile(self) -> None:
        """Value in the middle gets ~50%."""
        p = percentile_rank(3.0, [1.0, 2.0, 3.0, 4.0, 5.0])
        assert p == pytest.approx(40.0)  # 2 out of 5 are less

    def test_empty_history(self) -> None:
        """Empty history returns 50%."""
        p = percentile_rank(5.0, [])
        assert p == pytest.approx(50.0)


class TestRollingStats:
    """Test rolling statistics tracker."""

    def test_not_ready_below_min(self) -> None:
        """Stats not ready when below minimum observations."""
        stats = RollingStats(feature_name="AP", min_observations=21)
        for i in range(20):
            stats.add(float(i), date(2024, 1, i + 1))
        assert not stats.is_ready

    def test_ready_at_min(self) -> None:
        """Stats ready at minimum observations."""
        stats = RollingStats(feature_name="AP", min_observations=21)
        for i in range(21):
            stats.add(float(i), date(2024, 1, i + 1))
        assert stats.is_ready

    def test_mean_calculation(self) -> None:
        """Mean is correctly calculated from window."""
        stats = RollingStats(feature_name="RS", window=5, min_observations=3)
        for i in range(5):
            stats.add(float(i + 1), date(2024, 1, i + 1))
        assert stats.mean == pytest.approx(3.0)

    def test_window_eviction(self) -> None:
        """Old values are evicted when window is full."""
        stats = RollingStats(feature_name="AP", window=3, min_observations=2)
        stats.add(100.0, date(2024, 1, 1))
        stats.add(200.0, date(2024, 1, 2))
        stats.add(300.0, date(2024, 1, 3))
        stats.add(400.0, date(2024, 1, 4))  # Evicts 100.0
        assert stats.count == 3
        assert stats.values == [200.0, 300.0, 400.0]


class TestSectorRollingCalculator:
    """Test multi-sector rolling calculator."""

    def test_per_sector_independence(self) -> None:
        """Each sector's stats are independent."""
        calc = SectorRollingCalculator(
            tickers=("XLK", "XLF"),
            feature_names=("AP",),
            window=5,
            min_observations=3,
        )

        # Add different values to each sector
        for i in range(5):
            d = date(2024, 1, i + 1)
            calc.add_observation("XLK", d, {"AP": 100.0})
            calc.add_observation("XLF", d, {"AP": -100.0})

        xlk_stats = calc.get_stats("XLK", "AP")
        xlf_stats = calc.get_stats("XLF", "AP")

        assert xlk_stats is not None and xlk_stats.mean == pytest.approx(100.0)
        assert xlf_stats is not None and xlf_stats.mean == pytest.approx(-100.0)

    def test_zscore_not_clipped(self) -> None:
        """CRITICAL: Z-scores from calculator are NOT clipped."""
        calc = SectorRollingCalculator(
            tickers=("XLK",),
            feature_names=("AP",),
            window=63,
            min_observations=21,
        )

        rng = np.random.default_rng(42)
        values = rng.normal(0, 100, 63)

        for i, v in enumerate(values):
            d = date(2024, 1, 1) + timedelta(days=i)
            calc.add_observation("XLK", d, {"AP": float(v)})

        # Test with extreme value
        z = calc.get_zscore("XLK", "AP", 1000.0)
        assert z is not None
        assert abs(z) > 3.0  # Should NOT be clipped

    def test_insufficient_data_returns_none(self) -> None:
        """Z-score is None when insufficient history."""
        calc = SectorRollingCalculator(
            tickers=("XLK",),
            feature_names=("AP",),
            min_observations=21,
        )

        # Add only 10 observations
        for i in range(10):
            d = date(2024, 1, i + 1)
            calc.add_observation("XLK", d, {"AP": float(i)})

        z = calc.get_zscore("XLK", "AP", 5.0)
        assert z is None

    def test_ready_features(self) -> None:
        """Ready/not-ready feature tracking."""
        calc = SectorRollingCalculator(
            tickers=("XLK",),
            feature_names=("AP", "RS"),
            window=5,
            min_observations=3,
        )

        # Add only AP data
        for i in range(5):
            d = date(2024, 1, i + 1)
            calc.add_observation("XLK", d, {"AP": float(i)})

        assert "AP" in calc.get_ready_features("XLK")
        assert "RS" in calc.get_not_ready_features("XLK")
