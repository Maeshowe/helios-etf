"""
HELIOS ETF FLOW Streamlit Dashboard.

Displays sector allocation diagnostics.

Usage:
    uv run streamlit run helios/dashboard/app.py --server.port 8504
"""

from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from helios.core.types import AllocationState, HeliosResult
from helios.dashboard.components.allocation_card import render_allocation_card
from helios.dashboard.components.historical_chart import render_historical_chart
from helios.dashboard.components.sector_heatmap import STATE_COLORS, render_sector_heatmap

# Page config
st.set_page_config(
    page_title="HELIOS ETF FLOW",
    page_icon="\u2600",
    layout="wide",
)

# Sidebar
with st.sidebar:
    st.title("HELIOS ETF FLOW")
    st.caption("Sector-level Capital Allocation Diagnostic")

    st.divider()

    st.markdown("### Allocation States")
    for state_name, color in STATE_COLORS.items():
        st.markdown(
            f'<span style="color: {color};">\u25cf</span> **{state_name}**',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### Design Guardrails")
    st.markdown("""
    - Describes allocation, NOT signals
    - OVERWEIGHT != "buy"
    - UNDERWEIGHT != "sell"
    - No alerts generated
    - Daily data only
    """)

    st.divider()
    st.caption("CAS = 0.6 x AP + 0.4 x RS")
    st.caption("AP: Allocation Pressure (fund flows)")
    st.caption("RS: Relative Strength (vs SPY)")


def load_latest_result() -> tuple[HeliosResult | None, pd.DataFrame]:
    """Load the latest HELIOS result and history."""
    data_dir = Path("data/processed/helios")
    history_file = data_dir / "helios_history.parquet"

    history_df = pd.DataFrame()
    latest_result = None

    if history_file.exists():
        history_df = pd.read_parquet(history_file)
        history_df["date"] = pd.to_datetime(history_df["date"]).dt.date

        # Reconstruct latest HeliosResult from most recent date
        if not history_df.empty:
            latest_date = history_df["date"].max()
            latest_df = history_df[history_df["date"] == latest_date]

            from helios.core.types import BaselineStatus, SectorResult

            sectors = []
            for _, row in latest_df.iterrows():
                sectors.append(SectorResult(
                    ticker=row["ticker"],
                    allocation_score=row["allocation_score"],
                    state=AllocationState(row["state"]),
                    explanation=row.get("explanation", ""),
                    ap_zscore=row.get("ap_zscore", 0.0),
                    rs_zscore=row.get("rs_zscore", 0.0),
                    ap_raw=row.get("ap_raw", 0.0),
                    rs_raw=row.get("rs_raw", 0.0),
                    status=BaselineStatus(row.get("status", "COMPLETE")),
                ))

            overall_status = BaselineStatus.COMPLETE
            statuses = [s.status for s in sectors]
            if any(s == BaselineStatus.PARTIAL for s in statuses):
                overall_status = BaselineStatus.PARTIAL
            if all(s == BaselineStatus.INSUFFICIENT for s in statuses):
                overall_status = BaselineStatus.INSUFFICIENT

            latest_result = HeliosResult(
                trade_date=latest_date,
                sectors=tuple(sectors),
                status=overall_status,
            )

    return latest_result, history_df


# Main content
st.title("HELIOS ETF FLOW")
st.caption("Sector Capital Allocation Diagnostic")

result, history_df = load_latest_result()

if result is None:
    st.warning("No HELIOS data available. Run the daily pipeline first:")
    st.code("uv run python scripts/run_daily.py")
else:
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Date", str(result.trade_date))
    with col2:
        st.metric("Status", result.status.value)
    with col3:
        st.metric("Overweight", len(result.overweight_sectors))
    with col4:
        st.metric("Underweight", len(result.underweight_sectors))

    st.divider()

    # Sector heatmap
    render_sector_heatmap(result)

    st.divider()

    # Historical chart
    render_historical_chart(history_df)

    st.divider()

    # Per-sector details
    st.subheader("Sector Details")
    for sector in result.sectors:
        render_allocation_card(sector)

    # State distribution
    st.subheader("State Distribution")
    state_counts = Counter(s.state.value for s in result.sectors)
    dist_df = pd.DataFrame(
        [{"State": k, "Count": v} for k, v in sorted(state_counts.items())]
    )
    st.bar_chart(dist_df.set_index("State"))

    # Raw data expander
    with st.expander("Raw Data"):
        latest_df = history_df[history_df["date"] == result.trade_date]
        st.dataframe(latest_df, use_container_width=True)

    # JSON output expander
    with st.expander("JSON Output"):

        st.json(result.to_dict())
