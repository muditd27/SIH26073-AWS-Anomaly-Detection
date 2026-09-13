"""Page 1 — station picker. Click any AWS card to open the detail page."""

from __future__ import annotations


from data import STATIONS, anomaly_class
from ui import card_badge, card_health, humidity_label, sparkline


def station_card(station: dict) -> str:
    anom = anomaly_class(station["anomalyStatus"])
    icons = {"ok": "✓", "warn": "⚠", "bad": "⚠"}
    humidity = humidity_label(station["humidity"])
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
        <div class="anomaly-cell {anom}">{icons[anom]}<div><strong>{station['anomalyStatus']}</strong><span>Anomaly Status</span></div></div>
        <div class="time-cell">◷<div><strong>{station['lastUpdated']}</strong><span>Last Updated</span></div></div>
      </div>
    </a>
    """.splitlines())


def render_stations_page() -> str:
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
      {''.join(station_card(station) for station in STATIONS)}
    </div>
    <footer class="page-foot">
      <span>SkyGuard AI &nbsp;›&nbsp; Stations</span>
      <span class="tagline">Smarter Monitoring. Safer Tomorrow.</span>
    </footer>
    """.splitlines())
