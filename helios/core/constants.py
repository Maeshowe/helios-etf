"""
Constants for HELIOS ETF FLOW.

These values are FROZEN and must not be tuned or optimized.
They represent conceptual design choices, not fitted parameters.

HELIOS describes allocation, not direction.
"""

from typing import Final

# =============================================================================
# COMPONENT WEIGHTS (FROZEN)
# =============================================================================
# These weights are conceptual allocations, NOT optimized parameters.
# Do not tune these values.

WEIGHTS: Final[dict[str, float]] = {
    "AP": 0.60,  # Allocation Pressure (z-score of net fund flow)
    "RS": 0.40,  # Relative Strength (z-score of excess return vs SPY)
}

# Verify weights sum to 1.0
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

# =============================================================================
# NORMALIZATION PARAMETERS (FROZEN)
# =============================================================================

ROLLING_WINDOW: Final[int] = 63  # Trading days (~3 months)
MIN_OBSERVATIONS: Final[int] = 21  # Minimum for valid baseline (~1 month)

# =============================================================================
# STATE THRESHOLDS (FROZEN)
# =============================================================================
# CAS -> AllocationState mapping (operates in z-score space, NOT percentile)
# These describe WHERE capital is flowing, NOT whether to trade.

STATE_THRESHOLDS: Final[dict[str, tuple[float, float]]] = {
    "OVERWEIGHT": (1.0, float("inf")),  # CAS > +1.0σ
    "ACCUMULATING": (0.3, 1.0),  # +0.3 to +1.0
    "NEUTRAL": (-0.3, 0.3),  # -0.3 to +0.3
    "DECREASING": (-1.0, -0.3),  # -1.0 to -0.3
    "UNDERWEIGHT": (float("-inf"), -1.0),  # CAS < -1.0σ
}

# =============================================================================
# UNIVERSE (FROZEN)
# =============================================================================
# Fixed set of sector ETFs. No dynamic universe construction.

SECTOR_UNIVERSE: Final[tuple[str, ...]] = (
    "XLY",  # Consumer Discretionary
    "XLI",  # Industrials
    "XLF",  # Financials
    "XLE",  # Energy
    "XLK",  # Technology
    "XLP",  # Consumer Staples
    "XLV",  # Health Care
    "XLU",  # Utilities
    "XLB",  # Materials
    "XLRE",  # Real Estate
    "AGG",  # Aggregate Bond
)

BENCHMARK_TICKER: Final[str] = "SPY"

# =============================================================================
# SECTOR DISPLAY NAMES
# =============================================================================

SECTOR_NAMES: Final[dict[str, str]] = {
    "XLY": "Consumer Discretionary",
    "XLI": "Industrials",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLK": "Technology",
    "XLP": "Consumer Staples",
    "XLV": "Health Care",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "AGG": "Aggregate Bond",
}

# =============================================================================
# FEATURE NAMES
# =============================================================================

FEATURE_NAMES: Final[tuple[str, ...]] = ("AP", "RS")

# =============================================================================
# DESIGN DOCUMENTATION
# =============================================================================
# These constants encode the following design decisions:
#
# 1. NO Z-SCORE CLIPPING: Feature-level z-scores are NOT clipped.
#    Extreme values are preserved. CAS thresholds operate directly
#    in z-score space (no percentile ranking for classification).
#
# 2. ALLOCATION NOT DIRECTION: OVERWEIGHT means capital is flowing
#    into a sector, NOT a recommendation to buy. UNDERWEIGHT means
#    capital is flowing out, NOT a recommendation to sell.
#
# 3. FIXED UNIVERSE: The sector ETF universe is frozen.
#    No dynamic construction or screening.
#
# 4. TWO FEATURES: AP (flow-based) and RS (return-based) capture
#    different dimensions of capital allocation.
