"""
Composite Allocation Score (CAS) calculation.

CAS = 0.6 * AP + 0.4 * RS

Weights are FROZEN conceptual allocations, NOT optimized parameters.
"""

import logging

from helios.core.constants import WEIGHTS

logger = logging.getLogger(__name__)


def calculate_cas(z_scores: dict[str, float]) -> float:
    """
    Calculate Composite Allocation Score.

    CAS = 0.6 * z_AP + 0.4 * z_RS

    If only one feature is present (PARTIAL baseline), uses only
    that feature's contribution without rescaling.

    Args:
        z_scores: {"AP": float, "RS": float} -- NOT clipped

    Returns:
        CAS value (unbounded -- lives in z-score space)

    GUARDRAIL: CAS describes allocation pressure, NOT direction to trade.
    """
    weighted_sum = 0.0

    for name, weight in WEIGHTS.items():
        z = z_scores.get(name)
        if z is None:
            continue
        weighted_sum += weight * z

    return weighted_sum
