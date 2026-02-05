"""
Core type definitions for HELIOS ETF FLOW.

Defines enums, dataclasses, and type aliases for the sector allocation system.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import TypeAlias


class AllocationState(StrEnum):
    """
    Sector allocation states.

    These describe WHERE capital is flowing, NOT whether to trade.

    State Thresholds (CAS in z-score space):
        - OVERWEIGHT (> +1.0σ): Strong positive allocation pressure
        - ACCUMULATING (+0.3 to +1.0): Building allocation pressure
        - NEUTRAL (-0.3 to +0.3): Balanced allocation
        - DECREASING (-1.0 to -0.3): Declining allocation pressure
        - UNDERWEIGHT (< -1.0σ): Strong negative allocation pressure

    GUARDRAIL: OVERWEIGHT != "buy". UNDERWEIGHT != "sell".
    """

    OVERWEIGHT = "OVERWEIGHT"
    ACCUMULATING = "ACCUMULATING"
    NEUTRAL = "NEUTRAL"
    DECREASING = "DECREASING"
    UNDERWEIGHT = "UNDERWEIGHT"

    @classmethod
    def from_cas(cls, cas: float) -> "AllocationState":
        """
        Classify CAS into allocation state.

        Args:
            cas: Composite Allocation Score (unbounded z-score composite)

        Returns:
            Corresponding allocation state
        """
        if cas > 1.0:
            return cls.OVERWEIGHT
        elif cas > 0.3:
            return cls.ACCUMULATING
        elif cas >= -0.3:
            return cls.NEUTRAL
        elif cas >= -1.0:
            return cls.DECREASING
        else:
            return cls.UNDERWEIGHT

    @property
    def description(self) -> str:
        """Human-readable description of the state."""
        descriptions = {
            AllocationState.OVERWEIGHT: "Strong positive allocation pressure",
            AllocationState.ACCUMULATING: "Building allocation pressure",
            AllocationState.NEUTRAL: "Balanced allocation",
            AllocationState.DECREASING: "Declining allocation pressure",
            AllocationState.UNDERWEIGHT: "Strong negative allocation pressure",
        }
        return descriptions[self]


class BaselineStatus(StrEnum):
    """
    Status of baseline normalization.

    GUARDRAIL: INSUFFICIENT is assigned when critical data is missing.
    Better to report uncertainty than to guess.
    """

    COMPLETE = "COMPLETE"  # All features have sufficient history (n >= N_min)
    PARTIAL = "PARTIAL"  # Some features excluded (n < N_min)
    INSUFFICIENT = "INSUFFICIENT"  # Critical features missing, cannot compute


@dataclass(frozen=True)
class SectorResult:
    """
    Result for a single sector ETF on a single day.

    This is the per-sector output of the HELIOS engine.

    Design Notes:
        - allocation_score (CAS) is unbounded (lives in z-score space)
        - z-scores are NOT clipped to preserve tail information
        - State classification uses direct CAS thresholds, NOT percentile ranking
    """

    ticker: str
    allocation_score: float  # CAS value (unbounded z-score composite)
    state: AllocationState  # Classified allocation state
    explanation: str  # Human-readable explanation
    ap_zscore: float  # Allocation Pressure z-score
    rs_zscore: float  # Relative Strength z-score
    ap_raw: float  # Raw net flow value
    rs_raw: float  # Raw excess return value
    status: BaselineStatus  # Baseline completeness

    def to_dict(self) -> dict:
        """Convert to dictionary matching spec output format."""
        return {
            "allocation_score": round(self.allocation_score, 2),
            "state": self.state.value,
            "explanation": self.explanation,
            "ap_zscore": round(self.ap_zscore, 2),
            "rs_zscore": round(self.rs_zscore, 2),
            "ap_raw": round(self.ap_raw, 4),
            "rs_raw": round(self.rs_raw, 6),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class HeliosResult:
    """
    Complete HELIOS result for a single day (all sectors).

    This is the primary output of the HELIOS pipeline.
    """

    trade_date: date
    sectors: tuple[SectorResult, ...]
    status: BaselineStatus  # Overall baseline status

    def to_dict(self) -> dict:
        """Convert to dictionary matching spec output format."""
        result: dict = {"date": self.trade_date.isoformat()}
        for sector in self.sectors:
            result[sector.ticker] = {
                "allocation_score": round(sector.allocation_score, 2),
                "state": sector.state.value,
                "explanation": sector.explanation,
            }
        return result

    def get_sector(self, ticker: str) -> SectorResult | None:
        """Get result for a specific sector."""
        for sector in self.sectors:
            if sector.ticker == ticker:
                return sector
        return None

    @property
    def overweight_sectors(self) -> tuple[SectorResult, ...]:
        """Sectors in OVERWEIGHT state."""
        return tuple(s for s in self.sectors if s.state == AllocationState.OVERWEIGHT)

    @property
    def underweight_sectors(self) -> tuple[SectorResult, ...]:
        """Sectors in UNDERWEIGHT state."""
        return tuple(s for s in self.sectors if s.state == AllocationState.UNDERWEIGHT)


@dataclass
class SectorFeatureSet:
    """
    Raw and computed features for a single sector ETF.

    Contains inputs from data sources and computed metrics.
    The z-score normalization happens in the normalization module,
    not here.
    """

    ticker: str
    trade_date: date

    # Raw inputs
    net_flow: float | None = None  # Daily ETF net flow ($)
    etf_return: float | None = None  # Daily ETF return
    spy_return: float | None = None  # Daily SPY return

    # Computed feature (raw, before z-scoring)
    excess_return: float | None = None  # etf_return - spy_return

    # Normalized z-scores (populated by normalization pipeline)
    normalized: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "date": self.trade_date.isoformat(),
            "net_flow": self.net_flow,
            "etf_return": self.etf_return,
            "spy_return": self.spy_return,
            "excess_return": self.excess_return,
            "normalized": self.normalized,
        }


# Type aliases for clarity
ZScore: TypeAlias = float  # NOT clipped - preserves tail information
TradeDate: TypeAlias = date
Ticker: TypeAlias = str
