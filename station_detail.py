"""
Page 2–5 — Station Detail Work Page.
Shown after an AWS card is selected on Page 1 (Overview).
Features:
- Header with station identity, connectivity badge, circular health gauge, and status pill
- 5 KPI metric cards with synchronized baseline and aligned SHAP diagnostics
- 3 smooth physical Plotly trend graphs (Temp, Pres, RH) with diurnal corridors, unified hover tooltips (Actual, Expected, Delta), and click-to-fullscreen dialogs
- Dual tabs: [⚠️ Anomaly Log (N) & SHAP Explainability] and [📊 Raw Telemetry]
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


@st.dialog("Expanded Telemetry — Full-Screen Inspection", width="large")
def show_fullscreen_dialog(station_id: str, param_name: str, fig: go.Figure):
    st.markdown(f"### {param_name} — High Definition Waveform ({station_id})")
    st.caption("Interactive telemetry canvas with diurnal baseline, anomaly triggers, and precision hover inspection.")
    fs_fig = go.Figure(fig)
    fs_fig.update_layout(height=540, margin=dict(l=55, r=20, t=20, b=40))
    st.plotly_chart(fs_fig, width="stretch", config={"displayModeBar": True, "displaylogo": False})


def create_trend_chart(
    df: pd.DataFrame,
    actual_col: str,
    expected_col: str,
    unit: str,
    color_actual: str = "#f43f5e",
    color_expected: str = "#2563eb",
    corridor: float = 1.5,
    height: int = 210,
) -> go.Figure:
    """Builds interactive Plotly chart with diurnal confidence corridor, smooth curves, and unified hover tooltips."""
    fig = go.Figure()

    if not df.empty and actual_col in df.columns and expected_col in df.columns:
        x_vals = df["timestamp"] if "timestamp" in df.columns else df["label"]
        actual_vals = df[actual_col]
        expected_vals = df[expected_col]

        min_val = min(actual_vals.min(), expected_vals.min())
        max_val = max(actual_vals.max(), expected_vals.max())
        diff = max(max_val - min_val, 2.0)
        padding = max(diff * 0.18, 1.0)
        y_range = [min_val - padding, max_val + padding]

        # 1. Shaded diurnal confidence corridor around expected projection
        upper_bound = expected_vals + corridor
        lower_bound = expected_vals - corridor

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=upper_bound,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=lower_bound,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(37, 99, 235, 0.08)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # 2. Expected diurnal projection curve (dashed blue line)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=expected_vals,
                mode="lines",
                name="Expected Diurnal",
                line=dict(color=color_expected, width=2.2, dash="dash"),
                hovertemplate=f"┄ Expected: %{{y:.2f}} {unit}<extra></extra>",
            )
        )

        # 3. Preparation of rich hover inspection data for Actual curve
        deltas = []
        statuses = []
        for a, e in zip(actual_vals, expected_vals):
            d = a - e
            d_str = f"{'+' if d >= 0 else ''}{d:.2f}"
            deltas.append(d_str)
            if abs(d) > corridor * 1.5:
                statuses.append(f"⚠️ ANOMALY ({d_str} {unit})")
            else:
                statuses.append("✓ NOMINAL")

        custom_matrix = list(zip(x_vals, actual_vals, expected_vals, deltas, statuses))

        # 4. Actual sensor telemetry curve (solid vibrant line with hover info)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=actual_vals,
                mode="lines+markers",
                name="Actual Telemetry",
                line=dict(color=color_actual, width=2.4),
                marker=dict(size=4, color=color_actual),
                customdata=custom_matrix,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    + f"● <b>Actual:</b> %{{customdata[1]:.2f}} {unit}<br>"
                    + f"┄ <b>Expected:</b> %{{customdata[2]:.2f}} {unit}<br>"
                    + f"Δ <b>Residual:</b> %{{customdata[3]}} {unit}<br>"
                    + "⚡ <b>Status:</b> %{customdata[4]}"
                    + "<extra></extra>"
                ),
            )
        )

        # 5. Glowing alert markers on anomalous points
        anom_x = []
        anom_y = []
        for x, a, e in zip(x_vals, actual_vals, expected_vals):
            if abs(a - e) > corridor * 1.5:
                anom_x.append(x)
                anom_y.append(a)

        if anom_x:
            fig.add_trace(
                go.Scatter(
                    x=anom_x,
                    y=anom_y,
                    mode="markers",
                    name="Anomaly Trigger",
                    marker=dict(
                        size=9,
                        color="#ef4444",
                        symbol="circle",
                        line=dict(width=2.5, color="#ffffff"),
                    ),
                    hoverinfo="skip",
                )
            )
    else:
        y_range = [0, 100]

    fig.update_layout(
        height=height,
        margin=dict(l=45, r=15, t=8, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fafc",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#ffffff",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            bordercolor="#cbd5e1",
        ),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#94a3b8"),
            nticks=7,
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

    shap_data = station.get("shap_drivers", {"Temperature": 76, "Relative Humidity": 16, "Pressure": 8})
    shap_t = shap_data.get("Temperature", 70)
    shap_rh = shap_data.get("Relative Humidity", 20)
    shap_p = shap_data.get("Pressure", 10)
    primary_driver = station.get("primary_feature", "Temperature") if anomaly else "Nominal"

    anom_val_color = "#e11d48" if anomaly else "#16a34a"
    anom_dot_color = "#f43f5e" if anomaly else "#22c55e"
    card5_bg = "kpi--reason" if anomaly else "kpi--normal"
    anom_pill_class = "bad" if anomaly else "ok"
    anom_badge_label = f"{primary_driver.upper()} DRIVER" if anomaly else "NOMINAL BALANCE"

    # 1. Top Detail Header
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
    temp_diff = station.get('temperature', 25.0) - station.get('expectedTemp', 25.0)
    press_diff = station.get('pressure', 1013.0) - station.get('expectedPressure', 1013.0)
    hum_diff = station.get('humidity', 65.0) - station.get('expectedHumidity', 65.0)

    temp_badge = "bad" if abs(temp_diff) > 2.0 else "ok"
    press_badge = "bad" if abs(press_diff) > 3.0 else "ok"
    hum_badge = "bad" if abs(hum_diff) > 5.0 else "ok"

    kpis_html = f"""
    <div class="kpi-row">
      <article class="kpi kpi--temp">
        <div class="kpi-label"><span>🌡 Temperature</span><span class="badge {temp_badge}">{'ALERT' if temp_badge == 'bad' else 'NOMINAL'}</span></div>
        <div class="kpi-value">{station.get('temperature', 25.0):.1f} °C</div>
        <div class="kpi-sub">Expected: {station.get('expectedTemp', 25.0):.1f} °C &nbsp;|&nbsp; Δ: {delta(station.get('temperature', 25.0), station.get('expectedTemp', 25.0))} °C</div>
      </article>
      <article class="kpi kpi--press">
        <div class="kpi-label"><span>◎ Pressure</span><span class="badge {press_badge}">{'ALERT' if press_badge == 'bad' else 'NOMINAL'}</span></div>
        <div class="kpi-value">{station.get('pressure', 1013.0):.1f} hPa</div>
        <div class="kpi-sub">Expected: {station.get('expectedPressure', 1013.0):.1f} hPa &nbsp;|&nbsp; Δ: {delta(station.get('pressure', 1013.0), station.get('expectedPressure', 1013.0))} hPa</div>
      </article>
      <article class="kpi kpi--hum">
        <div class="kpi-label"><span>💧 Rel. Humidity</span><span class="badge {hum_badge}">{'ALERT' if hum_badge == 'bad' else 'NOMINAL'}</span></div>
        <div class="kpi-value">{humidity} %</div>
        <div class="kpi-sub">Expected: {station.get('expectedHumidity', 65.0):.1f} % &nbsp;|&nbsp; Δ: {delta(station.get('humidity', 65.0), station.get('expectedHumidity', 65.0))} %</div>
      </article>
      <article class="kpi kpi--score">
        <div class="kpi-label"><span>⚠ Threat Score</span><span class="badge {'bad' if anomaly else 'ok'}">{severity}</span></div>
        <div class="kpi-value">{station.get('anomalyScore', 0.12):.2f}</div>
        <div class="kpi-sub">Confidence: {station.get('confidence', 95)}% &nbsp;|&nbsp; {anom_type}</div>
      </article>
      <article class="kpi {card5_bg}">
        <div class="kpi-label"><span>🧠 SHAP Root Cause</span><span class="badge {anom_pill_class}">{anomaly_status}</span></div>
        <div class="kpi-value" style="font-size: 15px; color: {anom_val_color}; display:flex; align-items:center; gap:6px;">
          <span class="dot" style="background:{anom_dot_color};"></span>
          <span>{anom_badge_label}</span>
        </div>
        <div>
          <div class="shap-bar">
            <div class="shap-seg-temp" style="width:{shap_t}%;"></div>
            <div class="shap-seg-rh" style="width:{shap_rh}%;"></div>
            <div class="shap-seg-press" style="width:{shap_p}%;"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:10px; color:#64748b; font-weight:700;">
            <span>T: {shap_t}%</span><span>RH: {shap_rh}%</span><span>P: {shap_p}%</span>
          </div>
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
            <span class="legend"><i class="swatch swatch-actual"></i> Actual &nbsp; <i class="swatch swatch-expected"></i> Expected Diurnal</span>
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
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "responsive": True,
        }

        if not trend_df.empty:
            # 1. Temperature Chart
            c_t_head, c_t_fs = st.columns([0.80, 0.20])
            with c_t_head:
                render_html(f"<div style='font-size:13.5px; font-weight:700; color:#1e293b; margin-top:6px;'>🌡 Temperature (°C) &nbsp; <span class='badge {temp_badge}'>Current: {station.get('temperature', 25.0):.1f} °C</span></div>")
            fig_temp = create_trend_chart(trend_df, "tempActual", "tempExpected", "°C", color_actual="#f43f5e", color_expected="#2563eb", corridor=1.5, height=210)
            with c_t_fs:
                if st.button("⛶ Fullscreen", key=f"fs_t_{station['id']}", help="Expand temperature chart"):
                    show_fullscreen_dialog(station["id"], "Ambient Temperature (°C)", fig_temp)
            st.plotly_chart(fig_temp, width="stretch", config=plotly_config)

            # 2. Pressure Chart
            c_p_head, c_p_fs = st.columns([0.80, 0.20])
            with c_p_head:
                render_html(f"<div style='font-size:13.5px; font-weight:700; color:#1e293b; margin-top:6px;'>◎ Barometric Pressure (hPa) &nbsp; <span class='badge {press_badge}'>Current: {station.get('pressure', 1013.0):.1f} hPa</span></div>")
            fig_press = create_trend_chart(trend_df, "pressActual", "pressExpected", "hPa", color_actual="#0ea5e9", color_expected="#0369a1", corridor=2.0, height=210)
            with c_p_fs:
                if st.button("⛶ Fullscreen", key=f"fs_p_{station['id']}", help="Expand pressure chart"):
                    show_fullscreen_dialog(station["id"], "Barometric Pressure (hPa)", fig_press)
            st.plotly_chart(fig_press, width="stretch", config=plotly_config)

            # 3. Relative Humidity Chart
            c_h_head, c_h_fs = st.columns([0.80, 0.20])
            with c_h_head:
                render_html(f"<div style='font-size:13.5px; font-weight:700; color:#1e293b; margin-top:6px;'>💧 Relative Humidity (%) &nbsp; <span class='badge {hum_badge}'>Current: {humidity} %</span></div>")
            fig_hum = create_trend_chart(trend_df, "humActual", "humExpected", "%", color_actual="#10b981", color_expected="#047857", corridor=3.0, height=210)
            with c_h_fs:
                if st.button("⛶ Fullscreen", key=f"fs_h_{station['id']}", help="Expand humidity chart"):
                    show_fullscreen_dialog(station["id"], "Relative Humidity (%)", fig_hum)
            st.plotly_chart(fig_hum, width="stretch", config=plotly_config)

        else:
            st.info("No trend telemetry points recorded yet for this station.")

    with right:
        # Dual Tabs: [⚠️ Anomaly Log & SHAP (N)] and [📊 Raw Telemetry]
        anomalies_list = station.get("anomalies", [])
        tab_anomalies, tab_raw = st.tabs([
            f"⚠️ Anomaly Log ({len(anomalies_list)})",
            "📊 Raw Telemetry",
        ])

        with tab_anomalies:
            # SHAP Diagnostic Card
            shap_card_html = f"""
            <div class="panel" style="margin-bottom:12px; border-left: 4px solid {'#ef4444' if anomaly else '#22c55e'};">
              <div class="panel-head" style="margin-bottom:6px;">
                <h4 style="margin:0; font-size:13.5px; color:#1e293b;">🧠 SHAP Attribution Breakdown</h4>
                <span class="badge {anom_pill_class}">{primary_driver.upper()} DRIVER</span>
              </div>
              <p style="font-size:11.5px; color:#475569; line-height:1.4; margin:0 0 8px;">
                {reason}
              </p>
              <div style="margin-top:6px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
                  <span><b>🌡 Temperature:</b> {shap_t}% attribution</span>
                  <span style="color:#ef4444; font-weight:700;">{'Primary Driver' if primary_driver == 'Temperature' else 'Nominal'}</span>
                </div>
                <div style="background:#f1f5f9; height:6px; border-radius:99px; overflow:hidden; margin-bottom:6px;">
                  <div style="background:#ef4444; width:{shap_t}%; height:100%;"></div>
                </div>

                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
                  <span><b>💧 Rel. Humidity:</b> {shap_rh}% attribution</span>
                  <span style="color:#06b6d4; font-weight:700;">{'Secondary' if primary_driver == 'Temperature' else 'Nominal'}</span>
                </div>
                <div style="background:#f1f5f9; height:6px; border-radius:99px; overflow:hidden; margin-bottom:6px;">
                  <div style="background:#06b6d4; width:{shap_rh}%; height:100%;"></div>
                </div>

                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
                  <span><b>◎ Pressure:</b> {shap_p}% attribution</span>
                  <span style="color:#3b82f6; font-weight:700;">Baseline</span>
                </div>
                <div style="background:#f1f5f9; height:6px; border-radius:99px; overflow:hidden;">
                  <div style="background:#3b82f6; width:{shap_p}%; height:100%;"></div>
                </div>
              </div>
              <div style="margin-top:10px; font-size:11px; color:#64748b; background:#f8fafc; padding:6px 10px; border-radius:10px;">
                <b>Recommended Maintenance Action:</b> {action}
              </div>
            </div>
            """
            render_html(shap_card_html)

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
                        f"<td style='width:25%;'>"
                        f"<b>#{a.get('id', '—')}</b><br>"
                        f"<span style='color:#94a3b8; font-size:10px;'>{date_short} {time_short}</span>"
                        f"</td>"
                        f"<td style='width:25%;'>"
                        f"<span class='badge {badge_class}'>{sev}</span><br>"
                        f"<code style='font-size:10px; color:#475569;'>{a.get('type', 'ANOMALY')}</code>"
                        f"</td>"
                        f"<td style='width:50%; word-break:break-word;'>"
                        f"<div style='font-size:11px; font-weight:600; color:#1e293b; line-height:1.35;'>{a.get('message', 'Deviation detected')}</div>"
                        f"<div style='font-size:10px; color:#64748b; margin-top:3px;'><b>Action:</b> {a.get('action', 'Inspect')}</div>"
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
                        <th style="width:25%;">Alert ID</th>
                        <th style="width:25%;">Severity / Type</th>
                        <th style="width:50%;">Root Cause & Action</th>
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
                        <th style="width:10%;">#</th>
                        <th style="width:36%;">Timestamp</th>
                        <th style="width:18%;">Temp (°C)</th>
                        <th style="width:18%;">Pressure (hPa)</th>
                        <th style="width:18%;">Rel. Hum (%)</th>
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

    # 4. Fast Station Switcher & Footer
    footer_html = f"""
    <div class="panel" style="margin-top:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:12px; font-weight:700; color:#475569;">📍 Fast Switcher:</span>
        <a class="badge {'ok' if station['id']=='AWS001' else 'warn'}" href="?station=AWS001" target="_self" style="text-decoration:none;">AWS001</a>
        <a class="badge {'ok' if station['id']=='AWS002' else 'warn'}" href="?station=AWS002" target="_self" style="text-decoration:none;">AWS002</a>
        <a class="badge {'ok' if station['id']=='AWS003' else 'warn'}" href="?station=AWS003" target="_self" style="text-decoration:none;">AWS003</a>
        <a class="badge {'ok' if station['id']=='AWS004' else 'warn'}" href="?station=AWS004" target="_self" style="text-decoration:none;">AWS004</a>
      </div>
      <a class="home-btn" href="?" target="_self" style="width:auto; padding:6px 14px; font-size:12px; font-weight:700; gap:6px; display:inline-flex;">
        <span>⌂</span> All Weather Stations Hub
      </a>
    </div>
    <footer class="page-foot">
      <span><a href="?" target="_self">SkyGuard AI</a> &nbsp;›&nbsp; <a href="?" target="_self">Stations</a> &nbsp;›&nbsp; {station['id']}</span>
      <span class="tagline">Smarter Monitoring. Safer Tomorrow.</span>
    </footer>
    """
    render_html(footer_html)
