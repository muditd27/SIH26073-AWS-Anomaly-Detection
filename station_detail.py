"""
Page 2–5 — Station Detail Work Page.
Shown after an AWS card is selected on Page 1 (Overview).
Features:
- Header with station identity, connectivity badge, circular health gauge, and status pill
- 5 KPI metric cards: Temperature, Pressure, Relative Humidity, Anomaly Score, Anomaly Status & SHAP Reason
- 3 smooth physical Plotly trend graphs (Temp, Pres, RH) with unified hover tooltips (Actual, Expected, Delta)
  and sleek fullscreen expand controls
- Dual tabs: [⚠️ Anomaly Log (N)] and [📊 Raw Telemetry]
- Strictly no wind or weather columns per problem statement
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import connectivity_class, delta, generate_physical_trends, health_tone
from ui import health_ring, humidity_label, station_status_class


def render_html(html_str: str) -> None:
    """Renders HTML safely without leading indentation, eliminating markdown code block bugs."""
    clean = "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


def create_trend_chart(
    df: pd.DataFrame,
    actual_col: str,
    expected_col: str,
    title: str,
    unit: str,
    color_actual: str = "#f43f5e",
    color_expected: str = "#3b82f6",
    height: int = 215,
) -> go.Figure:
    """Builds interactive Plotly chart with smooth continuous curves and unified hover tooltips."""
    fig = go.Figure()

    if not df.empty and actual_col in df.columns and expected_col in df.columns:
        x_vals = df["timestamp"] if "timestamp" in df.columns else df["label"]
        actual_vals = df[actual_col]
        expected_vals = df[expected_col]

        min_val = min(actual_vals.min(), expected_vals.min())
        max_val = max(actual_vals.max(), expected_vals.max())
        diff = max(max_val - min_val, 2.0)
        padding = max(diff * 0.16, 1.0)
        y_range = [min_val - padding, max_val + padding]

        # Expected curve (dashed blue)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=expected_vals,
                mode="lines",
                name="Expected",
                line=dict(color=color_expected, width=2.2, dash="dash"),
                hovertemplate=f"<b>Expected</b>: %{{y:.2f}} {unit}<extra></extra>",
            )
        )

        # Actual curve (solid coral/red)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=actual_vals,
                mode="lines",
                name="Actual",
                line=dict(color=color_actual, width=2.2),
                hovertemplate=f"<b>Actual</b>: %{{y:.2f}} {unit}<extra></extra>",
            )
        )
    else:
        y_range = [0, 100]

    fig.update_layout(
        height=height,
        margin=dict(l=45, r=15, t=18, b=28),
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
    col1, col2 = st.columns([0.82, 0.18])
    with col1:
        st.subheader(f"🔍 Fullscreen Analysis — {chart_type} ({station['id']})")
    with col2:
        if st.button("✖ Close Fullscreen", key="btn_close_fs", type="primary", use_container_width=True):
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
    status_color = station_status_class(station.get("stationStatus", "Normal"))
    status_icon = "☀" if station.get("stationStatus", "Normal") == "Normal" else "⚠"

    humidity = humidity_label(station.get("humidity", 70.0))
    anom_type = station.get("anomalyType", "NORMAL")
    severity = station.get("severity", "NORMAL" if not anomaly else "CRITICAL" if "RAIL" in anom_type or "SPIKE" in anom_type else "MEDIUM")
    action = station.get("recommendedAction", "Routine inspection.")
    reason = station.get("reason", "Sensor operating normally within safe limits.")

    anom_val_color = "#e11d48" if anomaly else "#16a34a"
    anom_dot_color = "#f43f5e" if anomaly else "#22c55e"
    card5_bg = "kpi--reason" if anomaly else "kpi--normal"

    # 1. Top Detail Header (clean layout matching Image 2)
    top_html = f"""
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
          <span style="font-size:18px;">◷</span>
          <div><span>Last Recorded</span><br><strong>{station.get('lastRecorded', 'Live')}</strong></div>
        </div>
        <div class="meta-card meta-card--ring">
          {health_ring(station.get('sensorHealth', 95), tone, 48)}
          <span>Sensor Health</span>
        </div>
        <div class="meta-card">
          <span style="font-size:18px;">{status_icon}</span>
          <div><strong class="{status_color}">{station.get('stationStatus', 'Normal')}</strong><br><span>Station Status</span></div>
        </div>
      </div>
    </div>
    """
    render_html(top_html)

    # 2. 5 Perfectly Aligned KPI Cards
    kpis_html = f"""
    <div class="kpi-row">
      <article class="kpi kpi--temp">
        <div class="kpi-label">🌡 Temperature</div>
        <div class="kpi-value">{station.get('temperature', 25.0):.1f} °C</div>
        <div class="kpi-sub">Expected: {station.get('expectedTemp', 25.0):.1f} °C &nbsp;|&nbsp; Δ: {delta(station.get('temperature', 25.0), station.get('expectedTemp', 25.0))} °C</div>
      </article>
      <article class="kpi kpi--press">
        <div class="kpi-label">◎ Pressure</div>
        <div class="kpi-value">{station.get('pressure', 1013.0):.1f} hPa</div>
        <div class="kpi-sub">Expected: {station.get('expectedPressure', 1013.0):.1f} hPa &nbsp;|&nbsp; Δ: {delta(station.get('pressure', 1013.0), station.get('expectedPressure', 1013.0))} hPa</div>
      </article>
      <article class="kpi kpi--hum">
        <div class="kpi-label">💧 Relative Humidity</div>
        <div class="kpi-value">{humidity} %</div>
        <div class="kpi-sub">Expected: {station.get('expectedHumidity', 65.0):.1f} % &nbsp;|&nbsp; Δ: {delta(station.get('humidity', 65.0), station.get('expectedHumidity', 65.0))} %</div>
      </article>
      <article class="kpi kpi--score">
        <div class="kpi-label">⚠ Anomaly Score</div>
        <div class="kpi-value">{station.get('anomalyScore', 0.12):.2f}</div>
        <div class="kpi-sub">Confidence {station.get('confidence', 95)}% &nbsp;|&nbsp; {severity}</div>
      </article>
      <article class="kpi {card5_bg}">
        <div class="kpi-label">⚠ Anomaly Status</div>
        <div class="kpi-value" style="font-size: 17px; color: {anom_val_color}; display:flex; align-items:center; gap:6px;">
          <span class="dot" style="background:{anom_dot_color};"></span> {anomaly_status.upper()}
        </div>
        <div class="kpi-sub" style="font-size:11px; line-height:1.35;">
          <b>SHAP:</b> {reason}
        </div>
      </article>
    </div>
    """
    render_html(kpis_html)

    # 3. Main Workspace: Left Column (3 Trend Graphs) | Right Column (Dual Tabs)
    left, right = st.columns([1.18, 0.82], gap="medium")

    with left:
        panel_head_html = """
        <div class="panel">
          <div class="panel-head">
            <h3>📈 Actual vs Expected Sensor Trends</h3>
            <span class="legend"><i class="swatch swatch-actual"></i> Actual &nbsp; <i class="swatch swatch-expected"></i> Expected</span>
          </div>
        </div>
        """
        render_html(panel_head_html)

        col_range, col_info = st.columns([0.65, 0.35])
        with col_range:
            range_key = st.radio(
                "Range",
                ["3M", "1M", "7D"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"range_{station['id']}",
            )
        with col_info:
            st.caption("💡 Hover to inspect unified values & Δ error.")

        # Generate smooth natural physical trends for this station and range
        trend_records = generate_physical_trends(station["id"], range_key)
        trend_df = pd.DataFrame(trend_records)

        plotly_config = {
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["zoom2d", "pan2d", "resetScale2d"],
            "responsive": True,
        }

        # Fullscreen Modal View
        if st.session_state.get("fullscreen_chart"):
            render_fullscreen_modal(station, st.session_state["fullscreen_chart"], trend_df)

        if not trend_df.empty:
            # 1. Temperature Chart
            head_col1, head_col2 = st.columns([0.80, 0.20])
            with head_col1:
                render_html("<div style='font-size:13px; font-weight:700; color:#1e293b; padding-top:4px;'>🌡 Temperature (°C)</div>")
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_temp", use_container_width=True):
                    st.session_state["fullscreen_chart"] = "Temperature"
                    st.rerun()

            fig_temp = create_trend_chart(trend_df, "tempActual", "tempExpected", "Temperature (°C)", "°C")
            st.plotly_chart(fig_temp, use_container_width=True, config=plotly_config)

            # 2. Pressure Chart
            head_col1, head_col2 = st.columns([0.80, 0.20])
            with head_col1:
                render_html("<div style='font-size:13px; font-weight:700; color:#1e293b; padding-top:4px;'>◎ Pressure (hPa)</div>")
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_press", use_container_width=True):
                    st.session_state["fullscreen_chart"] = "Pressure"
                    st.rerun()

            fig_press = create_trend_chart(trend_df, "pressActual", "pressExpected", "Pressure (hPa)", "hPa")
            st.plotly_chart(fig_press, use_container_width=True, config=plotly_config)

            # 3. Relative Humidity Chart
            head_col1, head_col2 = st.columns([0.80, 0.20])
            with head_col1:
                render_html("<div style='font-size:13px; font-weight:700; color:#1e293b; padding-top:4px;'>💧 Relative Humidity (%)</div>")
            with head_col2:
                if st.button("⛶ Fullscreen", key="btn_fs_hum", use_container_width=True):
                    st.session_state["fullscreen_chart"] = "Relative Humidity"
                    st.rerun()

            fig_hum = create_trend_chart(trend_df, "humActual", "humExpected", "Relative Humidity (%)", "%")
            st.plotly_chart(fig_hum, use_container_width=True, config=plotly_config)

        else:
            st.info("No trend telemetry points recorded yet for this station.")

    with right:
        # Dual Tabs: [⚠️ Anomaly Log (N)] and [📊 Raw Telemetry]
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
                    time_val = a.get("timestamp", "—")
                    time_short = time_val.split(" ")[-1] if " " in time_val else time_val
                    date_short = time_val.split(" ")[0] if " " in time_val else ""
                    rows.append(
                        f"<tr>"
                        f"<td style='width:28%;'>"
                        f"<b>#{a.get('id', '—')}</b><br>"
                        f"<span style='color:#94a3b8; font-size:10px;'>{date_short} {time_short}</span>"
                        f"</td>"
                        f"<td style='width:28%;'>"
                        f"<span class='badge {badge_class}'>{sev}</span><br>"
                        f"<code style='font-size:10px; color:#475569;'>{a.get('type', 'ANOMALY')}</code>"
                        f"</td>"
                        f"<td style='width:44%;'>"
                        f"<div style='font-size:11px; font-weight:600; color:#1e293b; line-height:1.3;'>{a.get('message', 'Deviation detected')}</div>"
                        f"<div style='font-size:10px; color:#64748b; margin-top:2px;'><b>Action:</b> {a.get('action', 'Inspect')}</div>"
                        f"</td>"
                        f"</tr>"
                    )

                anom_table_html = f"""
                <div class="panel">
                  <div class="panel-head" style="margin-bottom:8px;">
                    <h3>⚠️ Anomaly Event History</h3>
                    <span style="font-size:11px; color:#64748b;">{len(anomalies_list)} Events</span>
                  </div>
                  <table class="anom-table">
                    <thead>
                      <tr>
                        <th style="width:28%;">Alert ID</th>
                        <th style="width:28%;">Severity & Type</th>
                        <th style="width:44%;">SHAP Root Cause & Action</th>
                      </tr>
                    </thead>
                    <tbody>{''.join(rows)}</tbody>
                  </table>
                </div>
                """
                render_html(anom_table_html)
            else:
                empty_html = """
                <div class="panel" style="padding:24px; text-align:center;">
                  <div style="font-size:28px; margin-bottom:8px;">✅</div>
                  <h4 style="margin:0 0 6px; color:#16a34a;">No Active Anomalies</h4>
                  <p style="color:#64748b; font-size:12px; margin:0;">All sensors are operating within expected theoretical boundaries.</p>
                </div>
                """
                render_html(empty_html)

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
                raw_table_html = f"""
                <div class="panel">
                  <div class="panel-head" style="margin-bottom:8px;">
                    <h3>📋 Raw Telemetry History</h3>
                    <span style="font-size:11px; color:#64748b;">Latest 24 Readings</span>
                  </div>
                  <table class="raw-table">
                    <thead>
                      <tr>
                        <th>#</th><th>Timestamp</th><th>Temp (°C)</th><th>Pressure (hPa)</th><th>Rel. Hum (%)</th>
                      </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                  </table>
                </div>
                """
                render_html(raw_table_html)
            else:
                render_html("""
                <div class="panel">
                  <div class="panel-head"><h3>📋 Raw Telemetry History</h3></div>
                  <p style="color: #64748b; font-size: 13px;">No recent telemetry recorded for this station.</p>
                </div>
                """)

    footer_html = f"""
    <footer class="page-foot">
      <span><a href="?" target="_self">SkyGuard AI</a> &nbsp;›&nbsp; <a href="?" target="_self">Stations</a> &nbsp;›&nbsp; {station['id']}</span>
      <span class="tagline">Smarter Monitoring. Safer Tomorrow.</span>
    </footer>
    """
    render_html(footer_html)
