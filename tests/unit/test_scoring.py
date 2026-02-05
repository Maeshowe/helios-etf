"""Tests for composite scoring (CAS calculation)."""

import pytest

from helios.scoring.composite import calculate_cas


class TestCalculateCAS:
    """Test CAS = 0.6*AP + 0.4*RS calculation."""

    def test_both_features(self) -> None:
        """CAS with both AP and RS."""
        cas = calculate_cas({"AP": 1.0, "RS": 1.0})
        assert cas == pytest.approx(1.0)  # 0.6*1.0 + 0.4*1.0

    def test_weighted_correctly(self) -> None:
        """Weights are correctly applied."""
        cas = calculate_cas({"AP": 2.0, "RS": 0.0})
        assert cas == pytest.approx(1.2)  # 0.6*2.0 + 0.4*0.0

        cas = calculate_cas({"AP": 0.0, "RS": 2.0})
        assert cas == pytest.approx(0.8)  # 0.6*0.0 + 0.4*2.0

    def test_negative_features(self) -> None:
        """Negative z-scores produce negative CAS."""
        cas = calculate_cas({"AP": -1.5, "RS": -2.0})
        assert cas == pytest.approx(-1.7)  # 0.6*(-1.5) + 0.4*(-2.0)

    def test_only_ap(self) -> None:
        """CAS with only AP (RS missing)."""
        cas = calculate_cas({"AP": 2.0})
        assert cas == pytest.approx(1.2)  # 0.6*2.0

    def test_only_rs(self) -> None:
        """CAS with only RS (AP missing)."""
        cas = calculate_cas({"RS": 2.0})
        assert cas == pytest.approx(0.8)  # 0.4*2.0

    def test_empty_features(self) -> None:
        """CAS is 0.0 with no features."""
        cas = calculate_cas({})
        assert cas == pytest.approx(0.0)

    def test_extreme_zscores_not_clipped(self) -> None:
        """CRITICAL: Extreme z-scores flow through to CAS without clipping."""
        cas = calculate_cas({"AP": 5.0, "RS": 5.0})
        assert cas == pytest.approx(5.0)  # 0.6*5.0 + 0.4*5.0 = 5.0

    def test_mixed_directions(self) -> None:
        """AP positive, RS negative (divergent signals)."""
        cas = calculate_cas({"AP": 2.0, "RS": -2.0})
        assert cas == pytest.approx(0.4)  # 0.6*2.0 + 0.4*(-2.0) = 1.2 - 0.8

    def test_zero_features(self) -> None:
        """Both features at zero produces zero CAS."""
        cas = calculate_cas({"AP": 0.0, "RS": 0.0})
        assert cas == pytest.approx(0.0)
