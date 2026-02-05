"""Tests for explanation generator."""

import pytest

from helios.core.types import AllocationState, BaselineStatus
from helios.explain.generator import ExplanationGenerator


class TestExplanationGenerator:
    """Test per-sector explanation generation."""

    def setup_method(self) -> None:
        self.gen = ExplanationGenerator()

    def test_overweight_explanation(self) -> None:
        """OVERWEIGHT state produces correct headline."""
        text = self.gen.generate(
            ticker="XLK",
            state=AllocationState.OVERWEIGHT,
            ap_zscore=1.5,
            rs_zscore=1.2,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "net inflows" in text.lower() or "outperformance" in text.lower()
        assert "1.50" in text or "+1.50" in text

    def test_underweight_explanation(self) -> None:
        """UNDERWEIGHT state produces correct headline."""
        text = self.gen.generate(
            ticker="XLE",
            state=AllocationState.UNDERWEIGHT,
            ap_zscore=-1.8,
            rs_zscore=-1.5,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "outflows" in text.lower() or "underperformance" in text.lower()

    def test_neutral_explanation(self) -> None:
        """NEUTRAL state produces balanced description."""
        text = self.gen.generate(
            ticker="XLP",
            state=AllocationState.NEUTRAL,
            ap_zscore=0.1,
            rs_zscore=-0.1,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "balanced" in text.lower() or "in line" in text.lower()

    def test_excluded_features_noted(self) -> None:
        """Excluded features are mentioned in explanation."""
        text = self.gen.generate(
            ticker="XLB",
            state=AllocationState.NEUTRAL,
            ap_zscore=None,
            rs_zscore=0.5,
            excluded=["AP"],
            status=BaselineStatus.PARTIAL,
        )
        assert "AP" in text
        assert "excluded" in text.lower() or "insufficient" in text.lower()

    def test_insufficient_status_warning(self) -> None:
        """INSUFFICIENT status produces warning."""
        text = self.gen.generate(
            ticker="XLRE",
            state=AllocationState.NEUTRAL,
            ap_zscore=None,
            rs_zscore=None,
            excluded=["AP", "RS"],
            status=BaselineStatus.INSUFFICIENT,
        )
        assert "insufficient" in text.lower()

    def test_complete_status_no_warning(self) -> None:
        """COMPLETE status has no extra warning."""
        text = self.gen.generate(
            ticker="XLK",
            state=AllocationState.ACCUMULATING,
            ap_zscore=0.6,
            rs_zscore=0.4,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "insufficient" not in text.lower()
        assert "excluded" not in text.lower()

    def test_driver_direction_elevated(self) -> None:
        """High z-score shows 'elevated' direction."""
        text = self.gen.generate(
            ticker="XLK",
            state=AllocationState.OVERWEIGHT,
            ap_zscore=2.0,
            rs_zscore=1.5,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "inflows" in text.lower() or "outperforming" in text.lower()

    def test_driver_direction_depressed(self) -> None:
        """Low z-score shows 'depressed' direction."""
        text = self.gen.generate(
            ticker="XLE",
            state=AllocationState.UNDERWEIGHT,
            ap_zscore=-2.0,
            rs_zscore=-1.5,
            excluded=[],
            status=BaselineStatus.COMPLETE,
        )
        assert "outflows" in text.lower() or "underperforming" in text.lower()

    def test_format_summary(self) -> None:
        """Summary format includes ticker and state."""
        summary = self.gen.format_summary("XLK", AllocationState.OVERWEIGHT, 1.24)
        assert "XLK" in summary
        assert "OVERWEIGHT" in summary
        assert "Technology" in summary
