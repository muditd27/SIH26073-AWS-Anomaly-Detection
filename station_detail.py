"""
Page 2–5 — Station Detail Work Page.
Shown after an AWS card is selected on Page 1 (Overview).
Features:
- Header with station identity, connectivity badge, circular health gauge, and status pill
- 5 KPI metric cards: Temperature, Pressure, Relative Humidity, Anomaly Score, Anomaly Status & SHAP Reason
- 3 interactive Plotly trend graphs (Temp, Pres, RH) with unified hover tooltips (Actual, Expected, Delta)
  and click-to-fullscreen expand modal/controls
- Dual tabs: [⚠️ Anomaly Log (N)] and [📊 Raw Telemetry]
- Strictly no wind or weather columns per problem statement
"""
from __future__ import annotations

import textwrap
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import connectivity_class, delta, filter_trend, health_tone
from ui import health_ring, humidity_label, station_status_class


def clean_html(value: str) -> str:
    return "\n".join(line.lstrip() for line in value.splitlines())


def create_trend_chart(
    df: pd.DataFrame,
    actual_col: str,
    expected_col: str,
    title: str,
    unit: str,
    color_actual: str = "#f43f5e",
    color_expected: str = "#3b82f6",
    height: int = 210,
) -> go.Figure:
    """Builds interactive Plotly chart with unified hover tooltips showing Actual, Expected & Delta."""
    fig = go.Figure()

    if not df.empty and actual_col in df.columns and expected_col in df.columns:
        x_vals = df["timestamp"] if "timestamp" in df.columns else df["label"]
        actual_vals = df[actual_col]
        expected_vals = df[expected_col]

        min_val = min(actual_vals.min(), expected_vals.min())
        max_val = max(actual_vals.max(), expected_vals.max())
        diff = max_val - min_val
        padding = max(diff * 0.12, 1.0)
        y_range = [min_val - padding, max_val + padding]

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=expected_vals,
                mode="lines",
                name="Expected",
                line=dict(color=color_expected, width=2, dash="dash"),
                hovertemplate=f"Expected: %{{y:.2f}} {unit}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=actual_vals,
                mode="lines+markers",
                name="Actual",
                marker=dict(size=4, color=color_actual),
                line=dict(color=color_actual, width=2.2),
                hovertemplate=f"Actual: %{{y:.2f}} {unit}<extra></extra>",
            )
        )
    else:
        y_range = [0, 100]

    fig.update_layout(
        height=height,
        margin=dict(l=45, r=15, t=32, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fafc",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#ffffff",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            bordercolor="#cbd5e1",
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#64748b"),
        ),
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=13, color="#1e293b"),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#94a3b8"),
            nticks=6,
        ),
        yaxis=dict(
            range=y_range,
            showgrid=True,
            gridcolor="#edf2f8",
            tickfont=dict(size=10, color="#94a3b8"),
            title=dict(text=unit, font=dict(size=10, color="#94a3b8")),
        ),
    )
    return fig


def render_fullscreen_modal(station: dict, chart_type: str, trend_df: pd.DataFrame) -> None:
    """Renders expanded fullscreen view for the selected sensor graph."""
    st.markdown("---")
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.subheader(f"🔍 Fullscreen Analysis — {chart_type} ({station['id']})")
    with col2:
        if st.button("✖ Close Fullscreen", key="btn_close_fs", type="secondary"):
            st.session_state["fullscreen_chart"] = None
            st.rerun()

    if chart_type == "Temperature":
        fig = create_trend_chart(trend_df, "tempActual", "tempExpected", "Temperature Trend Analysis", "°C", height=450)
    elif chart_type == "Pressure":
        fig = create_trend_chart(trend_df, "pressActual", "pressExpected", "Barometric Pressure Analysis", "hPa", height=450)
    else:
        fig = create_trend_chart(trend_df, "humActual", "humExpected", "Relative Humidity Analysis", "%", height=450)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})
    st.markdown("---")


def render_station_detail(station: dict) -> None:
    conn = connectivity_class(station.get("connectivity", "Online"))
    tone = health_tone(station.get("sensorHealth", 95))
    anomaly_status = station.get("anomalyStatus", "Normal")
    anomaly = anomaly_status != "Normal"
    alert = "kpi--alert" if anomaly else ""
    status_color = station_status_class(station.get("stationStatus", "Normal"))
    anom_color = "bad-text" if anomaly else "ok-text"
    status_icon = "☀" if station.get("stationStatus", "Normal") == "Normal" else "⚠"

    humidity = humidity_label(station.get("humidity", 70.0))
    anom_type = station.get("anomalyType", "NORMAL")
    severity = station.get("severity", "NORMAL" if not anomaly else "HIGH")
    action = station.get("recommendedAction", "Routine inspection and baseline monitoring.")
    reason = station.get("reason", "Sensor operating normally within safe limits.")

    # 1. Top Detail Header (matches Image 2)
    st.markdown(
        textwrap.dedent(f"""
        <div class="detail-head">
          <div class="detail-title">
            <div class="antenna">📡</div>
            <div>
              <div class="idrow">
                <h1>{station['id']}</h1>
                <span class="badge {conn}"><span class="dot"></span>{station.get('connectivity', 'Online')}</span>
              </div>
              <p class="station-name">{station.get('name', 'Station')}</p>
            </div>
          </div>
          <div class="detail-meta">
            <div class="meta-card">
              ◷
              <div><span>Last Recorded</span><br><strong>{station.get('lastRecorded', 'Live')}</strong></div>
            </div>
            <div class="meta-card meta-card--ring">
              {health_ring(station.get('sensorHealth', 95), tone, 58)}
              <span>Sensor Health</span>
            </div>
            <div class="meta-card">
              {status_icon}
              <div><strong class="{status_color}">{station.get('stationStatus', 'Normal')}</strong><br><span>Station Status</span></div>
            </div>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # 2. 5 KPI Metric Cards Row (matches Image 2)
    st.markdown(
        textwrap.dedent(f"""
        <div class="kpi-row">
          <article class="kpi kpi--temp">
            <div class="kpi-label">🌡 Temperature</div>
            <div class="kpi-value">{station.get('temperature', 25.0):.1f} °C</div>
            <div class="kpi-sub">Expected: {station.get('expectedTemp', 25.0):.1f} °C | Δ: {delta(station.get('temperature', 25.0), station.get('expectedTemp', 25.0))} °C</div>
          </article>
          <article class="kpi kpi--press">
            <div class="kpi-label">◎ Pressure</div>
            <div class="kpi-value">{station.get('pressure', 1013.0):.1f} hPa</div>
            <div class="kpi-sub">Expected: {station.get('expectedPressure', 1013.0):.1f} hPa | Δ: {delta(station.get('pressure', 1013.0), station.get('expectedPressure', 1013.0))} hPa</div>
          </article>
          <article class="kpi kpi--hum">
            <div class="kpi-label">💧 Relative Humidity</div>
            <div class="kpi-value">{humidity} %</div>
            <div class="kpi-sub">Expected: {station.get('expectedHumidity', 65.0):.1f} % | Δ: {delta(station.get('humidity', 65.0), station.get('expectedHumidity', 65.0))} %</div>
          </article>
          <article class="kpi kpi--score {alert}">
            <div class="kpi-label">⚠ Anomaly Score</div>
            <div class="kpi-value">{station.get('anomalyScore', 0.12):.2f}</div>
            <div class="kpi-sub">Confidence {station.get('confidence', 95)}% | Severity: {severity}</div>
          </article>
          <article class="kpi kpi--reason {alert}">
            <div class="kpi-label">⚠ Anomaly & Explanation ({anom_type})</div>
            <strong class="{anom_color}" style="font-size:16px;">{anomaly_status.upper()}</strong>
            <p><strong>SHAP Reason:</strong> {reason}</p>
            <p style="margin-top:4px; font-size:11px; color:#475569;"><strong>Action:</strong> {action}</p>
          </article>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # 3. Main Workspace Grid: Left Column (3 Trend Graphs) | Right Column (Dual Tabs)
    left, right = st.columns([1.18, 0.82], gap="medium")

    with left:
        st.markdown(
            textwrap.dedent("""
            <div class="panel">
              <div class="panel-head">
                <h3>📈 Actual vs Expected Sensor Trends</h3>
                <span class="legend"><i class="swatch swatch-actual"></i> Actual &nbsp; <i class="swatch swatch-expected"></i> Expected</span>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        col_range, col_info = st.columns([0.6, 0.4])
        with col_range:
            range_key = st.radio(
                "Range",
                ["3M", "1M", "7D"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"range_{station['id']}",
            )
        with col_info:
            st.caption("💡 Hover to inspect unified values & Δ error. Click ⛶ to expand.")

        raw_trend = station.get("trend", [])
        filtered_trend = filter_trend(raw_trend, range_key)
        trend_df = pd.DataFrame(filtered_trend)

        plotly_config = {
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["zoom2d", "pan2d", "resetScale2d"],
            "responsive": True,
        }

        if st.session_state.get("fullscreen_chart"):
            render_fullscreen_modal(station, st.session_state["fullscreen_chart"], trend_df)

        if not trend_df.empty:
            head_col1, head_col2 = st.columns([0.85, 0.15])
            with head_col1:
                st.markdown("<div style='font-size:13px; font-weight:700; color:#1e293b; margin-top:8px;'>🌡 Temperature (°C)</div>", unsafe_allow_html=True)
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_temp", help="View Temperature chart full screen"):
                    st.session_state["fullscreen_chart"] = "Temperature"
                    st.rerun()

            fig_temp = create_trend_chart(trend_df, "tempActual", "tempExpected", "Temperature (°C)", "°C")
            st.plotly_chart(fig_temp, use_container_width=True, config=plotly_config)

            head_col1, head_col2 = st.columns([0.85, 0.15])
            with head_col1:
                st.markdown("<div style='font-size:13px; font-weight:700; color:#1e293b; margin-top:8px;'>◎ Pressure (hPa)</div>", unsafe_allow_html=True)
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_press", help="View Pressure chart full screen"):
                    st.session_state["fullscreen_chart"] = "Pressure"
                    st.rerun()

            fig_press = create_trend_chart(trend_df, "pressActual", "pressExpected", "Pressure (hPa)", "hPa")
            st.plotly_chart(fig_press, use_container_width=True, config=plotly_config)

            head_col1, head_col2 = st.columns([0.85, 0.15])
            with head_col1:
                st.markdown("<div style='font-size:13px; font-weight:700; color:#1e293b; margin-top:8px;'>💧 Relative Humidity (%)</div>", unsafe_allow_html=True)
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_hum", help="View Humidity chart full screen"):
                    st.session_state["fullscreen_chart"] = "Relative Humidity"
                    st.rerun()

            fig_hum = create_trend_chart(trend_df, "humActual", "humExpected", "Relative Humidity (%)", "%")
            st.plotly_chart(fig_hum, use_container_width=True, config=plotly_config)

        else:
            st.info("No trend telemetry points recorded yet for this station.")

    with right:
        anomalies_list = station.get("anomalies", [])
        tab_anomalies, tab_raw = st.tabs([
            f"⚠️ Anomaly Log ({len(anomalies_list)})",
            "📊 Raw Telemetry",
        ])

        with tab_anomalies:
            if anomalies_list:
                rows = []
                for a in anomalies_list:
                    sev = a.get("severity", "MEDIUM")
                    badge_class = "bad" if sev in ["CRITICAL", "HIGH"] else "warn" if sev == "MEDIUM" else "ok"
                    rows.append(
                        f"<tr>"
                        f"<td><b>#{a.get('alert_id', a.get('id', '—'))}</b></td>"
                        f"<td>{a.get('created_at', a.get('timestamp', '—'))}</td>"
                        f"<td><span class='badge {badge_class}'>{sev}</span></td>"
                        f"<td><code>{a.get('type', a.get('anomaly_type', 'ANOMALY'))}</code></td>"
                        f"<td style='font-size:11px; color:#334155;'>{a.get('message', a.get('reason', 'Deviation detected'))}</td>"
                        f"</tr>"
                    )

                st.markdown(
                    textwrap.dedent(f"""
                    <div class="panel">
                      <div class="panel-head">
                        <h3>⚠️ Anomaly Event History</h3>
                      </div>
                      <table class="raw">
                        <thead>
                          <tr>
                            <th>ID</th><th>Time</th><th>Severity</th><th>Type</th><th>SHAP Root Cause / Detail</th>
                          </tr>
                        </thead>
                        <tbody>{''.join(rows)}</tbody>
                      </table>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    textwrap.dedent("""
                    <div class="panel" style="padding:20px; text-align:center;">
                      <div style="font-size:24px; margin-bottom:8px;">✅</div>
                      <h4 style="margin:0 0 4px; color:#16a34a;">No Active Anomalies</h4>
                      <p style="color:#64748b; font-size:12px; margin:0;">All sensors are operating within expected theoretical boundaries.</p>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )

        with tab_raw:
            readings = station.get("readings", [])
            if readings:
                rows = "".join(
                    f"<tr>"
                    f"<td>{row.get('id', idx + 1)}</td>"
                    f"<td>{row.get('timestamp', '—')}</td>"
                    f"<td><b>{row.get('temp', 0.0):.1f}</b></td>"
                    f"<td><b>{row.get('pressure', 0.0):.1f}</b></td>"
                    f"<td><b>{row.get('humidity', 0.0):.1f}</b></td>"
                    f"</tr>"
                    for idx, row in enumerate(readings)
                )
                st.markdown(
                    textwrap.dedent(f"""
                    <div class="panel">
                      <div class="panel-head">
                        <h3>📋 Raw Telemetry History</h3>
                        <span>Latest 10 Readings</span>
                      </div>
                      <table class="raw">
                        <thead>
                          <tr>
                            <th>#</th><th>Timestamp</th><th>Temp (°C)</th><th>Pressure (hPa)</th><th>Rel. Hum (%)</th>
                          </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                      </table>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    textwrap.dedent("""
                    <div class="panel">
                      <div class="panel-head"><h3>📋 Raw Telemetry History</h3></div>
                      <p style="color: #64748b; font-size: 13px;">No recent telemetry recorded for this station.</p>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )

    st.markdown(
        textwrap.dedent(f"""
        <footer class="page-foot">
          <span><a href="?" target="_self">SkyGuard AI</a> &nbsp;›&nbsp; <a href="?" target="_self">Stations</a> &nbsp;›&nbsp; {station['id']}</span>
          <span class="tagline">Smarter Monitoring. Safer Tomorrow.</span>
        </footer>
        """),
        unsafe_allow_html=True,
    )
