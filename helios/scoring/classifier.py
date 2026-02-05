"""
CAS state classifier for HELIOS ETF FLOW.

Classifies Composite Allocation Score into allocation states.
Thresholds operate directly in z-score space (NOT percentile).

GUARDRAIL: States describe allocation direction, NOT trading signals.
"""

from helios.core.types import AllocationState


def classify_state(cas: float) -> AllocationState:
    """
    Classify CAS into allocation state.

    Thresholds are FROZEN:
        > +1.0σ  -> OVERWEIGHT
        +0.3 to +1.0 -> ACCUMULATING
        -0.3 to +0.3 -> NEUTRAL
        -1.0 to -0.3 -> DECREASING
        < -1.0σ -> UNDERWEIGHT

    Args:
        cas: Composite Allocation Score (unbounded)

    Returns:
        AllocationState classification

    GUARDRAIL: This describes allocation direction, NOT a trading signal.
    """
    return AllocationState.from_cas(cas)
