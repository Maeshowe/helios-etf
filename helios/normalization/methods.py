"""
Normalization methods for HELIOS ETF FLOW.

CRITICAL DESIGN DECISION:
Z-scores are NOT clipped at the feature level.
Extreme values (tail information) must be preserved.
CAS thresholds operate directly in z-score space.

Rationale:
- Fund flow distributions have fat tails
- Extreme inflows/outflows are meaningful allocation signals
- Clipping would mask exactly the events we want to describe
"""

import logging
from collections.abc import Sequence

import numpy as np

logger = logging.getLogger(__name__)


def zscore_normalize(
    value: float,
    mean: float,
    std: float,
) -> float:
    """
    Calculate z-score normalization.

    IMPORTANT: This function does NOT clip the z-score.
    Extreme values are preserved to capture tail information.

    Args:
        value: The value to normalize
        mean: The rolling mean
        std: The rolling standard deviation

    Returns:
        Z-score (unbounded - NOT clipped)
    """
    if std == 0 or std is None or np.isnan(std):
        logger.debug(f"Zero std for value={value}, mean={mean}, returning 0.0")
        return 0.0

    z = (value - mean) / std

    # NO CLIPPING - preserve tail information
    # Extreme z-scores (e.g., -5, +7) indicate significant allocation shifts

    return float(z)


def percentile_rank(
    value: float,
    history: Sequence[float],
) -> float:
    """
    Calculate percentile rank of a value within historical distribution.

    NOTE: In HELIOS, percentile ranking is available for optional
    dashboard display ONLY. State classification uses CAS thresholds
    directly in z-score space (no percentile ranking needed).

    Args:
        value: The value to rank
        history: Historical values to compare against

    Returns:
        Percentile rank in [0, 100]
    """
    if not history:
        return 50.0

    n = len(history)
    count_less = sum(1 for h in history if h < value)
    percentile = (count_less / n) * 100

    return float(percentile)


def calculate_rolling_mean(
    values: Sequence[float],
    window: int,
) -> float | None:
    """
    Calculate rolling mean from recent values.

    Args:
        values: Sequence of historical values (oldest to newest)
        window: Number of values to include

    Returns:
        Rolling mean or None if insufficient data
    """
    if len(values) < window:
        return None

    recent = values[-window:]
    return float(np.mean(recent))


def calculate_rolling_std(
    values: Sequence[float],
    window: int,
    ddof: int = 1,
) -> float | None:
    """
    Calculate rolling standard deviation from recent values.

    Args:
        values: Sequence of historical values (oldest to newest)
        window: Number of values to include
        ddof: Delta degrees of freedom (default 1 for sample std)

    Returns:
        Rolling std or None if insufficient data
    """
    if len(values) < window:
        return None

    recent = values[-window:]
    return float(np.std(recent, ddof=ddof))
