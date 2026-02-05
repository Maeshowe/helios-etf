"""Tests for Allocation Pressure (AP) feature calculator."""

import pytest

from helios.features.allocation_pressure import AllocationPressure, APResult


class TestAllocationPressure:
    """Test AP raw value extraction."""

    def setup_method(self) -> None:
        self.calc = AllocationPressure()

    def test_positive_flow(self) -> None:
        """Positive net flow produces valid result."""
        result = self.calc.calculate("XLK", 500_000_000)
        assert result.is_valid
        assert result.net_flow == 500_000_000
        assert result.ticker == "XLK"

    def test_negative_flow(self) -> None:
        """Negative net flow produces valid result."""
        result = self.calc.calculate("XLE", -200_000_000)
        assert result.is_valid
        assert result.net_flow == -200_000_000

    def test_zero_flow(self) -> None:
        """Zero net flow produces valid result."""
        result = self.calc.calculate("XLP", 0.0)
        assert result.is_valid
        assert result.net_flow == 0.0

    def test_none_flow(self) -> None:
        """None net flow produces invalid result."""
        result = self.calc.calculate("XLB", None)
        assert not result.is_valid
        assert result.net_flow is None

    def test_large_flow(self) -> None:
        """Very large flow is preserved (no clipping at feature level)."""
        large_flow = 5_000_000_000  # $5B
        result = self.calc.calculate("XLK", large_flow)
        assert result.is_valid
        assert result.net_flow == large_flow

    def test_result_is_frozen(self) -> None:
        """APResult is immutable."""
        result = self.calc.calculate("XLK", 100_000_000)
        with pytest.raises(AttributeError):
            result.net_flow = 0  # type: ignore[misc]
