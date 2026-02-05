"""
Pytest fixtures for HELIOS ETF FLOW tests.
"""

from datetime import date

import numpy as np
import pytest

from helios.core.types import SectorFeatureSet


@pytest.fixture
def trade_date() -> date:
    """Standard test date."""
    return date(2024, 6, 15)


@pytest.fixture
def sector_tickers() -> tuple[str, ...]:
    """Subset of sector tickers for testing."""
    return ("XLK", "XLF", "XLE", "XLP", "XLV")


@pytest.fixture
def overweight_features(trade_date: date) -> SectorFeatureSet:
    """Features that should produce OVERWEIGHT state (with sufficient baseline)."""
    return SectorFeatureSet(
        ticker="XLK",
        trade_date=trade_date,
        net_flow=500_000_000,  # Large positive inflow
        etf_return=0.02,  # 2% return
        spy_return=0.005,  # 0.5% SPY return
        excess_return=0.015,  # 1.5% excess
    )


@pytest.fixture
def underweight_features(trade_date: date) -> SectorFeatureSet:
    """Features that should produce UNDERWEIGHT state (with sufficient baseline)."""
    return SectorFeatureSet(
        ticker="XLE",
        trade_date=trade_date,
        net_flow=-400_000_000,  # Large outflow
        etf_return=-0.015,  # -1.5% return
        spy_return=0.005,  # 0.5% SPY return
        excess_return=-0.02,  # -2% excess
    )


@pytest.fixture
def neutral_features(trade_date: date) -> SectorFeatureSet:
    """Features that should produce NEUTRAL state (with sufficient baseline)."""
    return SectorFeatureSet(
        ticker="XLP",
        trade_date=trade_date,
        net_flow=10_000_000,  # Small inflow
        etf_return=0.005,  # 0.5% return
        spy_return=0.005,  # 0.5% SPY return
        excess_return=0.0,  # Zero excess
    )


@pytest.fixture
def missing_flow_features(trade_date: date) -> SectorFeatureSet:
    """Features with missing flow data."""
    return SectorFeatureSet(
        ticker="XLB",
        trade_date=trade_date,
        net_flow=None,  # Missing
        etf_return=0.01,
        spy_return=0.005,
        excess_return=0.005,
    )


@pytest.fixture
def missing_all_features(trade_date: date) -> SectorFeatureSet:
    """Features with all data missing."""
    return SectorFeatureSet(
        ticker="XLRE",
        trade_date=trade_date,
        net_flow=None,
        etf_return=None,
        spy_return=None,
        excess_return=None,
    )


@pytest.fixture
def sufficient_flow_history() -> list[float]:
    """63 days of flow history for rolling stats."""
    rng = np.random.default_rng(42)
    return list(rng.normal(0, 100_000_000, 63))


@pytest.fixture
def sufficient_return_history() -> list[float]:
    """63 days of excess return history."""
    rng = np.random.default_rng(42)
    return list(rng.normal(0, 0.01, 63))


@pytest.fixture
def trade_dates_63() -> list[date]:
    """63 sequential trade dates for history."""
    from datetime import timedelta

    start = date(2024, 3, 1)
    dates = []
    current = start
    while len(dates) < 63:
        if current.weekday() < 5:  # Skip weekends
            dates.append(current)
        current += timedelta(days=1)
    return dates
