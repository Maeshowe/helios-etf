"""
Relative Strength (RS) feature calculator.

RS = z(Return_ETF - Return_SPY) -- z-score of excess return vs SPY.

The raw excess return is calculated here.
Z-score normalization happens in the normalization module.

GUARDRAIL: RS describes relative performance, NOT a momentum signal.
Positive RS means the sector is outperforming SPY.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RSResult:
    """Result of Relative Strength calculation."""

    ticker: str
    etf_return: float | None
    spy_return: float | None
    excess_return: float | None  # etf_return - spy_return
    is_valid: bool


class RelativeStrength:
    """
    Relative Strength (RS) feature calculator.

    Calculates excess return for a sector ETF vs SPY.
    The z-score normalization happens in the normalization module.
    """

    def calculate(
        self,
        ticker: str,
        etf_return: float | None,
        spy_return: float | None,
    ) -> RSResult:
        """
        Calculate excess return for a sector ETF vs SPY.

        Args:
            ticker: ETF ticker symbol
            etf_return: Daily ETF return (None if unavailable)
            spy_return: Daily SPY return (None if unavailable)

        Returns:
            RSResult with excess return and validity flag
        """
        if etf_return is None or spy_return is None:
            return RSResult(
                ticker=ticker,
                etf_return=etf_return,
                spy_return=spy_return,
                excess_return=None,
                is_valid=False,
            )

        excess_return = etf_return - spy_return

        return RSResult(
            ticker=ticker,
            etf_return=etf_return,
            spy_return=spy_return,
            excess_return=excess_return,
            is_valid=True,
        )
