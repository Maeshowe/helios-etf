"""
Feature aggregator for HELIOS ETF FLOW.

Combines AP and RS calculations per sector into unified SectorFeatureSet.
"""

import logging
from datetime import date

from helios.core.constants import SECTOR_UNIVERSE
from helios.core.types import SectorFeatureSet
from helios.features.allocation_pressure import AllocationPressure
from helios.features.relative_strength import RelativeStrength

logger = logging.getLogger(__name__)


class FeatureAggregator:
    """Aggregates AP and RS features per sector ETF."""

    def __init__(self) -> None:
        self.ap_calc = AllocationPressure()
        self.rs_calc = RelativeStrength()

    def calculate_sector(
        self,
        ticker: str,
        trade_date: date,
        net_flow: float | None,
        etf_return: float | None,
        spy_return: float | None,
    ) -> SectorFeatureSet:
        """
        Calculate features for a single sector ETF.

        Args:
            ticker: ETF ticker symbol
            trade_date: Date of observation
            net_flow: Daily net fund flow in dollars
            etf_return: Daily ETF return
            spy_return: Daily SPY return

        Returns:
            SectorFeatureSet with raw feature values
        """
        ap_result = self.ap_calc.calculate(ticker, net_flow)
        rs_result = self.rs_calc.calculate(ticker, etf_return, spy_return)

        return SectorFeatureSet(
            ticker=ticker,
            trade_date=trade_date,
            net_flow=ap_result.net_flow,
            etf_return=rs_result.etf_return,
            spy_return=rs_result.spy_return,
            excess_return=rs_result.excess_return,
        )

    def calculate_all(
        self,
        trade_date: date,
        flows: dict[str, float | None],
        returns: dict[str, float | None],
        spy_return: float | None,
    ) -> dict[str, SectorFeatureSet]:
        """
        Calculate features for all sector ETFs.

        Args:
            trade_date: Date of observation
            flows: {ticker: net_flow} for each sector
            returns: {ticker: etf_return} for each sector
            spy_return: Daily SPY return (shared across all sectors)

        Returns:
            {ticker: SectorFeatureSet} for all sectors
        """
        results: dict[str, SectorFeatureSet] = {}

        for ticker in SECTOR_UNIVERSE:
            net_flow = flows.get(ticker)
            etf_return = returns.get(ticker)

            features = self.calculate_sector(
                ticker=ticker,
                trade_date=trade_date,
                net_flow=net_flow,
                etf_return=etf_return,
                spy_return=spy_return,
            )
            results[ticker] = features

            logger.debug(
                f"{ticker}: flow={net_flow}, return={etf_return}, "
                f"spy={spy_return}, excess={features.excess_return}"
            )

        logger.info(f"Calculated features for {len(results)} sectors")
        return results
