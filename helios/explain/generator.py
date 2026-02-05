"""
Explanation generator for HELIOS ETF FLOW.

Generates human-readable explanations of sector allocation states.
"""

import logging
from collections.abc import Sequence

from helios.core.constants import SECTOR_NAMES
from helios.core.types import AllocationState, BaselineStatus
from helios.explain.templates import DRIVER_TEMPLATES, STATE_TEMPLATES, STATUS_TEMPLATES

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """
    Generates human-readable explanations for sector allocation states.

    Combines:
    - State-level interpretation
    - Sector name context
    - Driver analysis (AP and RS contributions)
    - Status notes
    """

    def generate(
        self,
        ticker: str,
        state: AllocationState,
        ap_zscore: float | None,
        rs_zscore: float | None,
        excluded: Sequence[str],
        status: BaselineStatus,
    ) -> str:
        """
        Generate explanation for a single sector.

        Args:
            ticker: Sector ETF ticker
            state: Classified allocation state
            ap_zscore: AP z-score (None if excluded)
            rs_zscore: RS z-score (None if excluded)
            excluded: List of excluded feature names
            status: Baseline status

        Returns:
            Human-readable explanation string
        """
        parts: list[str] = []

        # 1. State headline
        state_text = STATE_TEMPLATES.get(state, state.description)
        parts.append(state_text)

        # 2. Driver details
        driver_parts: list[str] = []
        if ap_zscore is not None:
            direction = self._get_direction(ap_zscore)
            template = DRIVER_TEMPLATES["AP"][direction]
            driver_parts.append(f"{template} ({ap_zscore:+.2f}\u03c3)")

        if rs_zscore is not None:
            direction = self._get_direction(rs_zscore)
            template = DRIVER_TEMPLATES["RS"][direction]
            driver_parts.append(f"{template} ({rs_zscore:+.2f}\u03c3)")

        if driver_parts:
            parts.append(" ".join(driver_parts) + ".")

        # 3. Status notes
        status_text = STATUS_TEMPLATES.get(status.value, "")
        if status_text:
            parts.append(status_text)

        # 4. Excluded features
        if excluded:
            parts.append(f"Excluded: {', '.join(excluded)}.")

        return " ".join(parts)

    @staticmethod
    def _get_direction(zscore: float) -> str:
        """Classify z-score into directional label."""
        if zscore > 0.5:
            return "elevated"
        elif zscore < -0.5:
            return "depressed"
        else:
            return "neutral"

    def format_summary(
        self,
        ticker: str,
        state: AllocationState,
        cas: float,
    ) -> str:
        """
        Format one-line summary.

        Args:
            ticker: Sector ETF ticker
            state: Allocation state
            cas: Composite Allocation Score

        Returns:
            One-line summary
        """
        sector_name = SECTOR_NAMES.get(ticker, ticker)
        return f"{sector_name} ({ticker}): {cas:+.2f} ({state.value})"
