"""Tests for Relative Strength (RS) feature calculator."""

import pytest

from helios.features.relative_strength import RelativeStrength, RSResult


class TestRelativeStrength:
    """Test RS excess return calculation."""

    def setup_method(self) -> None:
        self.calc = RelativeStrength()

    def test_outperformance(self) -> None:
        """ETF outperforming SPY produces positive excess return."""
        result = self.calc.calculate("XLK", etf_return=0.02, spy_return=0.005)
        assert result.is_valid
        assert result.excess_return == pytest.approx(0.015)

    def test_underperformance(self) -> None:
        """ETF underperforming SPY produces negative excess return."""
        result = self.calc.calculate("XLE", etf_return=-0.01, spy_return=0.005)
        assert result.is_valid
        assert result.excess_return == pytest.approx(-0.015)

    def test_same_return_as_spy(self) -> None:
        """Same return as SPY produces zero excess return."""
        result = self.calc.calculate("XLP", etf_return=0.005, spy_return=0.005)
        assert result.is_valid
        assert result.excess_return == pytest.approx(0.0)

    def test_none_etf_return(self) -> None:
        """Missing ETF return produces invalid result."""
        result = self.calc.calculate("XLB", etf_return=None, spy_return=0.005)
        assert not result.is_valid
        assert result.excess_return is None

    def test_none_spy_return(self) -> None:
        """Missing SPY return produces invalid result."""
        result = self.calc.calculate("XLF", etf_return=0.01, spy_return=None)
        assert not result.is_valid
        assert result.excess_return is None

    def test_both_none(self) -> None:
        """Both missing produces invalid result."""
        result = self.calc.calculate("XLU", etf_return=None, spy_return=None)
        assert not result.is_valid

    def test_both_negative(self) -> None:
        """Both negative returns, ETF less negative = positive excess."""
        result = self.calc.calculate("XLV", etf_return=-0.005, spy_return=-0.02)
        assert result.is_valid
        assert result.excess_return == pytest.approx(0.015)

    def test_result_is_frozen(self) -> None:
        """RSResult is immutable."""
        result = self.calc.calculate("XLK", 0.01, 0.005)
        with pytest.raises(AttributeError):
            result.excess_return = 0  # type: ignore[misc]
