"""
Allocation Pressure (AP) feature calculator.

AP = z(NetFlow) -- the z-score of daily net ETF fund flow.

The raw net flow value is extracted here.
Z-score normalization happens in the normalization module.

GUARDRAIL: AP describes capital flow direction, NOT a buy/sell signal.
Positive AP means net inflows; negative means net outflows.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class APResult:
    """Result of Allocation Pressure calculation."""

    ticker: str
    net_flow: float | None  # Raw daily net flow in dollars
    is_valid: bool


class AllocationPressure:
    """
    Allocation Pressure (AP) feature calculator.

    Extracts the raw net flow value for a sector ETF.
    The z-score normalization happens in the normalization module.
    """

    def calculate(self, ticker: str, net_flow: float | None) -> APResult:
        """
        Extract the raw net flow value for a sector ETF.

        Args:
            ticker: ETF ticker symbol
            net_flow: Daily net fund flow in dollars (None if unavailable)

        Returns:
            APResult with raw value and validity flag
        """
        if net_flow is None:
            return APResult(ticker=ticker, net_flow=None, is_valid=False)

        return APResult(ticker=ticker, net_flow=net_flow, is_valid=True)
