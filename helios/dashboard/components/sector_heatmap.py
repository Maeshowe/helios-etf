"""
Sector heatmap component for HELIOS dashboard.

Displays a color-coded grid of sector allocation states.
"""

import streamlit as st

from helios.core.constants import SECTOR_NAMES
from helios.core.types import HeliosResult

STATE_COLORS: dict[str, str] = {
    "OVERWEIGHT": "#22c55e",
    "ACCUMULATING": "#84cc16",
    "NEUTRAL": "#6b7280",
    "DECREASING": "#f59e0b",
    "UNDERWEIGHT": "#ef4444",
}


def render_sector_heatmap(result: HeliosResult) -> None:
    """Render the sector allocation heatmap."""
    st.subheader("Sector Allocation Map")

    # Create grid layout (4 columns)
    cols = st.columns(4)

    for i, sector in enumerate(result.sectors):
        col = cols[i % 4]
        color = STATE_COLORS.get(sector.state.value, "#6b7280")
        name = SECTOR_NAMES.get(sector.ticker, sector.ticker)

        with col:
            st.markdown(
                f"""
                <div style="
                    background-color: {color};
                    color: white;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 4px 0;
                    text-align: center;
                ">
                    <div style="font-weight: bold; font-size: 14px;">{sector.ticker}</div>
                    <div style="font-size: 11px; opacity: 0.9;">{name}</div>
                    <div style="font-size: 18px; font-weight: bold; margin: 4px 0;">
                        {sector.allocation_score:+.2f}
                    </div>
                    <div style="font-size: 11px;">{sector.state.value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
