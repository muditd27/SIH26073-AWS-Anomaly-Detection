"""Page 2 — station detail. Shown after an AWS card is selected on page 1."""

from __future__ import annotations

import textwrap
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import connectivity_class, delta, filter_trend, health_tone
from ui import health_ring, humidity_label, station_status_class


def trend_chart(df: pd.DataFrame, actual: str, expected: str, y_range: list[float], title: str) -> go.Figure:
    fig = go.Figure()
    if not df.empty and actual in df.columns and expected in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["label"],
                y=df[actual],
                name="Actual",
                line=dict(color="#f43f5e", width=1.8),
                hovertemplate="%{y}<extra>Actual</extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["label"],
                y=df[expected],
                name="Expected",
                line=dict(color="#3b82f6", width=1.8),
                hovertemplate="%{y}<extra>Expected</extra>",
            )
        )
    fig.update_layout(
        height=190,
        margin=dict(l=40, r=10, t=28, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title=dict(text=title, font=dict(size=12, color="#64748b"), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#94a3b8"), nticks=6),
        yaxis=dict(range=y_range, showgrid=True, gridcolor="#edf2f8", tickfont=dict(size=11, color="#94a3b8")),
    )
    return fig


def render_station_detail(station: dict) -> None:
    conn = connectivity_class(station["connectivity"])
    tone = health_tone(station["sensorHealth"])
    anomaly = station["anomalyStatus"] != "Normal"
    alert = "kpi--alert" if anomaly else ""
    status_color = station_status_class(station["stationStatus"])
    anom_color = "bad-text" if anomaly else "ok-text"
    status_icon = "☀" if station["stationStatus"] == "Normal" else "⚠"

    humidity = humidity_label(station["humidity"])
    anom_type = station.get("anomalyType", "NORMAL")
    severity = station.get("severity", "NORMAL")
    action = station.get("recommendedAction", "No action required.")

    st.markdown(
        textwrap.dedent(f"""
        <div class="detail-head">
          <div class="detail-title">
            <div class="antenna">📡</div>
            <div>
              <div class="idrow">
                <h1>{station['id']}</h1>
                <span class="badge {conn}"><span class="dot"></span>{station['connectivity']}</span>
              </div>
              <p class="station-name">{station['name']}</p>
            </div>
          </div>
          <div class="detail-meta">
            <div class="meta-card">◷<div><span>Last Recorded</span><br><strong>{station['lastRecorded']}</strong></div></div>
            <div class="meta-card meta-card--ring">{health_ring(station['sensorHealth'], tone, 58)}<span>Sensor Health</span></div>
            <div class="meta-card">{status_icon}<div><strong class="{status_color}">{station['stationStatus']}</strong><br><span>Station Status</span></div></div>
          </div>
        </div>
        <div class="kpi-row">
          <article class="kpi kpi--temp">
            <div class="kpi-label">🌡 Temperature</div>
            <div class="kpi-value">{station['temperature']:.1f} °C</div>
            <div class="kpi-sub">Expected: {station['expectedTemp']:.1f} °C | Error: {delta(station['temperature'], station['expectedTemp'])} °C</div>
          </article>
          <article class="kpi kpi--press">
            <div class="kpi-label">◎ Pressure</div>
            <div class="kpi-value">{station['pressure']:.1f} hPa</div>
            <div class="kpi-sub">Expected: {station['expectedPressure']:.1f} hPa | Error: {delta(station['pressure'], station['expectedPressure'])} hPa</div>
          </article>
          <article class="kpi kpi--hum">
            <div class="kpi-label">💧 Relative Humidity</div>
            <div class="kpi-value">{humidity} %</div>
            <div class="kpi-sub">Expected: {station['expectedHumidity']:.1f} % | Error: {delta(station['humidity'], station['expectedHumidity'])} %</div>
          </article>
          <article class="kpi kpi--score {alert}">
            <div class="kpi-label">⚠ Anomaly Score</div>
            <div class="kpi-value">{station['anomalyScore']:.2f}</div>
            <div class="kpi-sub">Confidence {station['confidence']}% | Severity: {severity}</div>
          </article>
          <article class="kpi kpi--reason {alert}">
            <div class="kpi-label">⚠ Anomaly & Explanation ({anom_type})</div>
            <strong class="{anom_color}">{station['anomalyStatus'].upper()}</strong>
            <p><strong>SHAP Reason:</strong> {station['reason']}</p>
            <p style="margin-top:4px; font-size:11px; color:#475569;"><strong>Action:</strong> {action}</p>
          </article>
        </div>
        """),
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 0.85], gap="medium")
    with left:
        st.markdown(
            textwrap.dedent("""
            <div class="panel">
              <div class="panel-head">
                <h3>📈 Actual vs Expected Sensor Trends</h3>
                <span class="legend"><i class="swatch swatch-actual"></i> Actual <i class="swatch swatch-expected"></i> Expected</span>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        range_key = st.radio(
            "Range",
            ["3M", "1M", "7D"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"range_{station['id']}",
        )
        raw_trend = station.get("trend", [])
        filtered_trend = filter_trend(raw_trend, range_key)
        trend = pd.DataFrame(filtered_trend)

        config = {"displayModeBar": False}
        if not trend.empty:
            st.plotly_chart(trend_chart(trend, "tempActual", "tempExpected", [-10, 50], "Temperature (°C)"), use_container_width=True, config=config)
            st.plotly_chart(trend_chart(trend, "pressActual", "pressExpected", [940, 1060], "Pressure (hPa)"), use_container_width=True, config=config)
            st.plotly_chart(trend_chart(trend, "humActual", "humExpected", [0, 100], "Relative Humidity (%)"), use_container_width=True, config=config)
        else:
            st.info("No trend telemetry points recorded yet.")

    with right:
        readings = station.get("readings", [])
        if readings:
            rows = "".join(
                f"<tr><td>{row['id']}</td><td>{row['timestamp']}</td><td>{row['temp']}</td>"
                f"<td>{row['pressure']}</td><td>{row['humidity']}</td></tr>"
                for row in readings
            )
            st.markdown(
                textwrap.dedent(f"""
                <div class="panel">
                  <div class="panel-head"><h3>📋 Raw Telemetry History <span>(Latest Readings)</span></h3></div>
                  <table class="raw">
                    <thead>
                      <tr>
                        <th>#</th><th>Timestamp</th><th>Temp (°C)</th><th>Pressure (hPa)</th><th>Rel. Humidity (%)</th>
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

        alerts = station.get("alerts", [])
        if alerts:
            alert_rows = "".join(
                f"<tr><td>#{a['alert_id']}</td><td>{a['created_at']}</td>"
                f"<td><span class='badge bad'>{a['severity']}</span></td>"
                f"<td>{a['message']}</td></tr>"
                for a in alerts
            )
            st.markdown(
                textwrap.dedent(f"""
                <div class="panel" style="margin-top: 12px;">
                  <div class="panel-head"><h3>🔔 Station Alerts & Anomalies</h3></div>
                  <table class="raw">
                    <thead>
                      <tr>
                        <th>ID</th><th>Created At</th><th>Severity</th><th>Message</th>
                      </tr>
                    </thead>
                    <tbody>{alert_rows}</tbody>
                  </table>
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
