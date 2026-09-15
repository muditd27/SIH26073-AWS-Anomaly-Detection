"""
Page 1 — station picker. Click any AWS card to open the detail page.
Matches Image 1 layout with 4 station cards and live network anomalies.
"""
from __future__ import annotations

from data import get_stations, anomaly_class
from ui import card_badge, card_health, humidity_label, sparkline


def station_card(station: dict) -> str:
    anom = anomaly_class(station.get("anomalyStatus", "Normal"))
    icons = {"ok": "✓", "warn": "⚠", "bad": "⚠"}
    humidity = humidity_label(station.get("humidity", 72.0))
    anom_type = station.get("anomalyType", "")
    anom_sub = f"Status ({anom_type})" if anom_type and anom_type != "NORMAL" else "Anomaly Status"

    return "\n".join(line.lstrip() for line in f"""
    <a class="station-card" href="?station={station['id']}" target="_self">
      <div class="station-card-top">
        <div class="led">{station['number']}</div>
        <div>
          <div class="idrow">
            <strong>{station['id']}</strong>
            <span class="badge {card_badge(station)}"><span class="dot"></span>{station['connectivity']}</span>
          </div>
          <div class="station-name">{station['name']}</div>
        </div>
        <span class="chevron">→</span>
      </div>
      <div class="metric-row">
        <div>🌡<b>{station['temperature']:.1f} °C</b><span>Temperature</span></div>
        <div>◎<b>{station['pressure']:.1f} hPa</b><span>Pressure</span></div>
        <div>💧<b>{humidity} %</b><span>Relative Humidity</span></div>
      </div>
      <div class="station-card-bottom">
        <div class="health-cell">{card_health(station)}<span>Sensor Health</span></div>
        <div class="anomaly-cell {anom}">{icons.get(anom, '✓')}<div><strong>{station['anomalyStatus']}</strong><span>{anom_sub}</span></div></div>
        <div class="time-cell">◷<div><strong>{station['lastUpdated']}</strong><span>Last Updated</span></div></div>
      </div>
    </a>
    """.splitlines())


def render_stations_page(stations: list[dict] | None = None) -> str:
    if stations is None:
        stations = get_stations()

    if not stations:
        cards_html = """
        <div class="panel" style="padding: 24px; text-align: center; grid-column: 1 / -1;">
          <h3>⚠️ Initializing SkyGuard AI Telemetry</h3>
          <p style="color: #64748b;">Loading telemetry and predictions...</p>
        </div>
        """
    else:
        cards_html = "".join(station_card(station) for station in stations)

    avg_t = sum(s["temperature"] for s in stations) / max(1, len(stations))
    avg_p = sum(s["pressure"] for s in stations) / max(1, len(stations))
    avg_h = sum(s["humidity"] for s in stations) / max(1, len(stations))
    alerts_count = sum(1 for s in stations if s.get("anomalyStatus") != "Normal")

    fleet_bar = f"""
    <div class="panel" style="margin: 12px 0 16px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; border-radius: 18px;">
      <div style="display:flex; align-items:center; gap:10px;">
        <span class="dot"></span>
        <span style="font-size:13px; font-weight:700; color:#1e293b;">Network Health:</span>
        <span class="badge ok">{len(stations)} Stations Operational</span>
        <span class="badge {'bad' if alerts_count > 0 else 'ok'}">{alerts_count} Flagged Anomalies</span>
      </div>
      <div style="display:flex; align-items:center; gap:18px; font-size:12px; color:#64748b;">
        <span>🌡 Mean Temp: <b style="color:#1e293b;">{avg_t:.1f} °C</b></span>
        <span>◎ Mean Pressure: <b style="color:#1e293b;">{avg_p:.1f} hPa</b></span>
        <span>💧 Mean Humidity: <b style="color:#1e293b;">{avg_h:.1f} %</b></span>
      </div>
    </div>
    """

    return "\n".join(line.lstrip() for line in f"""
    <section class="hero">
      <div>
        <p class="eyebrow">AI-POWERED WEATHER MONITORING</p>
        <h1>Welcome to SkyGuard AI</h1>
        <p class="hero-copy">
          Monitor your AWS network in real-time with AI-driven anomaly detection.<br>
          Select a station below to view detailed insights, sensor readings, and ML predictions.
        </p>
      </div>
      <div class="hero-visual">
        <div class="spark-wrap">
          <div class="hero-alert">⚠ Anomaly Detected</div>
          {sparkline()}
        </div>
        <ul class="pipeline">
          <li>✓ Detect</li>
          <li>✓ Analyze</li>
          <li>✓ Report</li>
        </ul>
      </div>
    </section>
    {fleet_bar}
    <section class="section-head">
      <div>📍</div>
      <div>
        <h2>Select a Weather Station</h2>
        <p>Choose a station to view live data, AI predictions, and anomaly insights.</p>
      </div>
    </section>
    <div class="station-grid">
      {cards_html}
    </div>
    <footer class="page-foot">
      <span>SkyGuard AI &nbsp;›&nbsp; Stations</span>
      <span class="tagline">Smarter Monitoring. Safer Tomorrow.</span>
    </footer>
    """.splitlines())
