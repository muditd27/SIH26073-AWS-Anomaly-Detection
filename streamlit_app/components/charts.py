"""
Plotly chart generator for SkyGuard AI Streamlit application.
Renders high-definition dual-line charts: Actual vs Expected with hover tooltips and dynamic Y-axis scaling.
"""

from typing import List, Dict, Any, Optional
import plotly.graph_objects as go


def create_dual_line_chart(
    title: str,
    unit: str,
    timestamps: List[str],
    labels: List[str],
    actual: List[float],
    expected: List[float],
    actual_color: str = "#ef4444",
    expected_color: str = "#0284c7",
    height: int = 210,
) -> go.Figure:
    """
    Creates an interactive dual-line Plotly chart matching SkyGuard AI visual style:
    - Actual: Coral/Red line
    - Expected: Cyan/Blue line
    - Custom hover tooltips with delta difference
    - Dynamic Y-axis scaling with 12% headroom & footroom
    """
    fig = go.Figure()

    # Calculate differences for hover
    deltas = []
    for a, e in zip(actual, expected):
        if a is not None and e is not None:
            d = a - e
            sign = "+" if d >= 0 else ""
            deltas.append(f"{sign}{d:.1f} {unit}")
        else:
            deltas.append("N/A")

    # Dynamic Y-axis scale based on data points with 12% padding
    all_vals = [v for v in (actual + expected) if v is not None and isinstance(v, (int, float))]
    if all_vals:
        d_min = min(all_vals)
        d_max = max(all_vals)
        pad = (d_max - d_min) * 0.12 if d_max > d_min else 2.0
        y_range = [d_min - pad, d_max + pad]
    else:
        y_range = [0, 100]

    # 1. Expected Trace (Cyan Blue)
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=expected,
            name="Expected",
            mode="lines",
            line=dict(color=expected_color, width=2.0),
            customdata=timestamps,
            hovertemplate=(
                "<b>Expected:</b> %{y:.1f} " + unit + "<br>"
                "<b>Date/Time:</b> %{customdata}<extra></extra>"
            ),
        )
    )

    # 2. Actual Trace (Coral Red)
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=actual,
            name="Actual",
            mode="lines",
            line=dict(color=actual_color, width=2.2),
            customdata=list(zip(timestamps, expected, deltas)),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "<span style='color:" + actual_color + "'>● Actual:</span> <b>%{y:.1f} " + unit + "</b><br>"
                "<span style='color:" + expected_color + "'>● Expected:</span> <b>%{customdata[1]:.1f} " + unit + "</b><br>"
                "Δ Difference: <b>%{customdata[2]}</b><extra></extra>"
            ),
        )
    )

    # Calculate tick step for x-axis so labels don't crowd
    tick_step = max(1, len(labels) // 7)
    tick_vals = [labels[i] for i in range(0, len(labels), tick_step)]

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=13, color="#334155", family="Inter, sans-serif"),
            x=0.01,
            y=0.96,
        ),
        margin=dict(l=35, r=20, t=32, b=28),
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.18,
            xanchor="right",
            x=0.99,
            font=dict(size=10, family="Inter, sans-serif", color="#64748b"),
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="#e2e8f0",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_vals,
            tickfont=dict(size=9, color="#64748b", family="Inter, sans-serif"),
        ),
        yaxis=dict(
            range=y_range,
            showgrid=True,
            gridcolor="#f1f5f9",
            gridwidth=1,
            showline=False,
            tickfont=dict(size=9, color="#94a3b8", family="Inter, sans-serif"),
        ),
    )

    return fig
