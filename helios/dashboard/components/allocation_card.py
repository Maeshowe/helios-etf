"""
Allocation card component for HELIOS dashboard.

Displays per-sector score card with CAS, state, and AP/RS breakdown.
"""

import streamlit as st

from helios.core.constants import SECTOR_NAMES
from helios.core.types import SectorResult
from helios.dashboard.components.sector_heatmap import STATE_COLORS


def render_allocation_card(sector: SectorResult) -> None:
    """Render detailed allocation card for a single sector."""
    name = SECTOR_NAMES.get(sector.ticker, sector.ticker)
    color = STATE_COLORS.get(sector.state.value, "#6b7280")

    st.markdown(f"### {sector.ticker} - {name}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="CAS",
            value=f"{sector.allocation_score:+.2f}",
        )

    with col2:
        st.markdown(
            f'<span style="color: {color}; font-weight: bold; font-size: 20px;">'
            f"{sector.state.value}</span>",
            unsafe_allow_html=True,
        )

    with col3:
        st.metric(label="Status", value=sector.status.value)

    # Driver breakdown
    col_ap, col_rs = st.columns(2)

    with col_ap:
        ap_arrow = "\u2191" if sector.ap_zscore > 0 else "\u2193" if sector.ap_zscore < 0 else "\u2192"
        st.metric(
            label=f"AP (Flow) {ap_arrow}",
            value=f"{sector.ap_zscore:+.2f}\u03c3",
        )

    with col_rs:
        rs_arrow = "\u2191" if sector.rs_zscore > 0 else "\u2193" if sector.rs_zscore < 0 else "\u2192"
        st.metric(
            label=f"RS (Strength) {rs_arrow}",
            value=f"{sector.rs_zscore:+.2f}\u03c3",
        )

    st.caption(sector.explanation)
    st.divider()
