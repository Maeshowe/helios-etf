"""Tests for CAS state classifier."""

import pytest

from helios.core.types import AllocationState
from helios.scoring.classifier import classify_state


class TestClassifyState:
    """Test CAS -> AllocationState classification."""

    def test_overweight(self) -> None:
        """CAS > +1.0 -> OVERWEIGHT."""
        assert classify_state(1.5) == AllocationState.OVERWEIGHT
        assert classify_state(2.0) == AllocationState.OVERWEIGHT
        assert classify_state(5.0) == AllocationState.OVERWEIGHT

    def test_accumulating(self) -> None:
        """CAS +0.3 to +1.0 -> ACCUMULATING."""
        assert classify_state(0.5) == AllocationState.ACCUMULATING
        assert classify_state(0.8) == AllocationState.ACCUMULATING
        assert classify_state(1.0) == AllocationState.ACCUMULATING

    def test_neutral(self) -> None:
        """CAS -0.3 to +0.3 -> NEUTRAL."""
        assert classify_state(0.0) == AllocationState.NEUTRAL
        assert classify_state(0.1) == AllocationState.NEUTRAL
        assert classify_state(-0.1) == AllocationState.NEUTRAL
        assert classify_state(0.3) == AllocationState.NEUTRAL  # boundary: 0.3 is NEUTRAL (> 0.3 for ACCUMULATING)

    def test_decreasing(self) -> None:
        """CAS -1.0 to -0.3 -> DECREASING."""
        assert classify_state(-0.5) == AllocationState.DECREASING
        assert classify_state(-0.8) == AllocationState.DECREASING
        assert classify_state(-1.0) == AllocationState.DECREASING

    def test_underweight(self) -> None:
        """CAS < -1.0 -> UNDERWEIGHT."""
        assert classify_state(-1.5) == AllocationState.UNDERWEIGHT
        assert classify_state(-2.0) == AllocationState.UNDERWEIGHT
        assert classify_state(-5.0) == AllocationState.UNDERWEIGHT

    # Boundary values

    def test_boundary_overweight(self) -> None:
        """CAS exactly 1.0 is ACCUMULATING (boundary: > 1.0 for OVERWEIGHT)."""
        assert classify_state(1.0) == AllocationState.ACCUMULATING

    def test_boundary_just_above_overweight(self) -> None:
        """CAS just above 1.0 is OVERWEIGHT."""
        assert classify_state(1.001) == AllocationState.OVERWEIGHT

    def test_boundary_accumulating_lower(self) -> None:
        """CAS exactly 0.3 is NEUTRAL (boundary: > 0.3 for ACCUMULATING)."""
        assert classify_state(0.3) == AllocationState.NEUTRAL

    def test_boundary_just_above_accumulating(self) -> None:
        """CAS just above 0.3 is ACCUMULATING."""
        assert classify_state(0.301) == AllocationState.ACCUMULATING

    def test_boundary_neutral_lower(self) -> None:
        """CAS exactly -0.3 is NEUTRAL (boundary: >= -0.3)."""
        assert classify_state(-0.3) == AllocationState.NEUTRAL

    def test_boundary_decreasing_start(self) -> None:
        """CAS just below -0.3 is DECREASING."""
        assert classify_state(-0.301) == AllocationState.DECREASING

    def test_boundary_underweight(self) -> None:
        """CAS exactly -1.0 is DECREASING (boundary: >= -1.0)."""
        assert classify_state(-1.0) == AllocationState.DECREASING

    def test_boundary_just_below_underweight(self) -> None:
        """CAS just below -1.0 is UNDERWEIGHT."""
        assert classify_state(-1.001) == AllocationState.UNDERWEIGHT

    def test_extreme_positive(self) -> None:
        """Very high CAS is still OVERWEIGHT (no upper bound)."""
        assert classify_state(100.0) == AllocationState.OVERWEIGHT

    def test_extreme_negative(self) -> None:
        """Very low CAS is still UNDERWEIGHT (no lower bound)."""
        assert classify_state(-100.0) == AllocationState.UNDERWEIGHT
