"""
Historical chart component for HELIOS dashboard.

Multi-line Plotly chart with CAS over time and threshold bands.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from helios.core.constants import SECTOR_NAMES


def render_historical_chart(history_df: pd.DataFrame) -> None:
    """
    Render CAS time series chart for all sectors.

    Args:
        history_df: DataFrame with date, ticker, allocation_score columns
    """
    if history_df.empty:
        st.info("No historical data available yet.")
        return

    st.subheader("Historical Allocation Scores")

    fig = go.Figure()

    # Add threshold bands
    fig.add_hline(y=1.0, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="OVERWEIGHT", annotation_position="top right")
    fig.add_hline(y=0.3, line_dash="dot", line_color="lightgreen", opacity=0.3)
    fig.add_hline(y=-0.3, line_dash="dot", line_color="orange", opacity=0.3)
    fig.add_hline(y=-1.0, line_dash="dash", line_color="red", opacity=0.5,
                  annotation_text="UNDERWEIGHT", annotation_position="bottom right")
    fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.2)

    # Add line per sector
    for ticker in history_df["ticker"].unique():
        sector_df = history_df[history_df["ticker"] == ticker].sort_values("date")
        name = SECTOR_NAMES.get(ticker, ticker)
        fig.add_trace(go.Scatter(
            x=sector_df["date"],
            y=sector_df["allocation_score"],
            mode="lines",
            name=f"{ticker} ({name})",
            hovertemplate=f"{ticker}<br>CAS: %{{y:+.2f}}<br>%{{x}}<extra></extra>",
        ))

    fig.update_layout(
        yaxis_title="Composite Allocation Score (CAS)",
        xaxis_title="Date",
        height=500,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
        margin={"l": 50, "r": 20, "t": 30, "b": 80},
    )

    st.plotly_chart(fig, use_container_width=True)
