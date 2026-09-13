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
