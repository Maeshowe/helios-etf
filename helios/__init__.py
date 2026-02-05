"""
HELIOS ETF FLOW - Sector-level Capital Allocation Diagnostic.

Measures where capital is being allocated across sectors
relative to the market. This is a diagnostic layer,
NOT a signal, NOT a timing tool, NOT a trend indicator.
"""

__version__ = "0.1.0"

from helios.core.types import (
    AllocationState,
    BaselineStatus,
    HeliosResult,
    SectorFeatureSet,
    SectorResult,
)

__all__ = [
    "AllocationState",
    "BaselineStatus",
    "HeliosResult",
    "SectorFeatureSet",
    "SectorResult",
    "__version__",
]
