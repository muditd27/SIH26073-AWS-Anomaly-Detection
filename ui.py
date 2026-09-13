from __future__ import annotations

import math

from data import LAST_UPDATED, connectivity_class, health_tone


def inject_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
  background:
    radial-gradient(1200px 500px at 85% -10%, #dbeafe 0%, transparent 55%),
    radial-gradient(900px 400px at 10% 0%, #e0f2fe 0%, transparent 50%),
    #eef5fd;
  font-family: 'Plus Jakarta Sans', sans-serif;
  color: #163a66;
}

[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, header, .stDeployButton,
section[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

.block-container {
  padding: 18px 1rem 28px !important;
  max-width: 1200px !important;
}

div[data-testid="stVerticalBlock"] > div { gap: 0.55rem; }

.topbar, .hero, .station-card, .panel, .kpi, .meta-card {
  background: #fff;
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 22px;
}
.topbar-left, .topbar-right, .brand, .nexora, .status-pill { display: flex; align-items: center; gap: 10px; }
.home-btn {
  width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center;
  color: #3b82f6; background: #eff6ff; text-decoration: none; font-size: 16px;
}
.brand-name { font-weight: 800; font-size: 16px; line-height: 1.1; }
.brand-sub { color: #7b93b0; font-size: 11px; }
.status-pill, .updated-pill { color: #4b6b8c; font-size: 13px; font-weight: 600; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,0.15); }
.nexora { font-weight: 800; color: #1e3a8a; padding-left: 12px; border-left: 1px solid #e6eef8; }

.hero {
  margin-top: 16px; padding: 28px 32px; border-radius: 28px;
  display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px;
  background:
    linear-gradient(120deg, rgba(255,255,255,0.92), rgba(239,246,255,0.75)),
    radial-gradient(500px 180px at 85% 20%, rgba(59,130,246,0.18), transparent);
}
.eyebrow { margin: 0 0 8px; letter-spacing: 0.18em; font-size: 11px; font-weight: 700; color: #60a5fa; }
.hero h1 { margin: 0; font-size: 34px; letter-spacing: -0.04em; }
.hero-copy { margin: 12px 0 0; color: #5b7694; line-height: 1.6; }
.hero-visual { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px; }
.spark-wrap { position: relative; }
.hero-alert {
  position: absolute; top: 8px; right: 8px;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 999px; background: #fff1f2; color: #e11d48;
  font-size: 11px; font-weight: 700; white-space: nowrap;
}
.pipeline { list-style: none; margin: 0; padding: 10px 12px; border-radius: 16px; background: rgba(255,255,255,0.8); border: 1px solid #e0edff; }
.pipeline li { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: #2563eb; padding: 6px 0; }

.section-head { display: flex; gap: 10px; align-items: flex-start; margin: 18px 0 8px; }
.section-head h2 { margin: 0; font-size: 20px; }
.section-head p { margin: 4px 0 0; color: #7b93b0; font-size: 13px; }

.station-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.station-card {
  display: block; padding: 18px 20px 16px; border-radius: 24px;
  text-decoration: none; color: inherit; transition: transform .18s ease, box-shadow .18s ease;
}
.station-card:hover { transform: translateY(-3px); box-shadow: 0 16px 36px rgba(37,99,235,0.14); }
.station-card-top { display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; }
.led {
  font-size: 40px; font-weight: 800; letter-spacing: 1px; line-height: 1;
  background: linear-gradient(180deg, #93c5fd 0%, #3b82f6 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.idrow { display: flex; align-items: center; gap: 10px; }
.idrow strong, .detail-title h1 { font-size: 20px; margin: 0; }
.station-name { color: #7b93b0; font-size: 13px; margin: 2px 0 0; }
.chevron { color: #93c5fd; font-size: 20px; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.badge .dot { width: 8px; height: 8px; box-shadow: none; }
.badge.ok { color: #16a34a; background: #ecfdf3; } .badge.ok .dot { background: #22c55e; }
.badge.warn { color: #d97706; background: #fff7ed; } .badge.warn .dot { background: #f59e0b; }
.badge.bad { color: #e11d48; background: #fff1f2; } .badge.bad .dot { background: #f43f5e; }

.metric-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 16px 0 14px; }
.metric-row b { font-size: 15px; display: block; }
.metric-row span, .health-cell span, .anomaly-cell span, .time-cell span, .meta-card span { color: #7b93b0; font-size: 11px; }
.station-card-bottom {
  display: grid; grid-template-columns: 0.9fr 1.2fr 1fr; gap: 10px; align-items: center;
  padding-top: 8px; border-top: 1px solid #e6eef8;
}
.health-ring { position: relative; display: grid; place-items: center; }
.health-ring span { position: absolute; font-size: 11px; font-weight: 800; color: #163a66; }
.health-cell, .anomaly-cell, .time-cell { display: flex; flex-direction: row; align-items: center; gap: 8px; }
.anomaly-cell strong { display: block; font-size: 13px; }
.anomaly-cell.ok strong { color: #16a34a; }
.anomaly-cell.warn strong { color: #d97706; }
.anomaly-cell.bad strong { color: #e11d48; }

.page-foot { display: flex; justify-content: space-between; margin-top: 14px; color: #7b93b0; font-size: 12px; }
.page-foot a { color: inherit; text-decoration: none; }
.tagline { color: #60a5fa; font-weight: 600; }

.detail-head { display: flex; justify-content: space-between; gap: 16px; margin-top: 16px; align-items: center; flex-wrap: wrap; }
.detail-title, .detail-meta { display: flex; align-items: center; gap: 12px; }
.antenna { width: 54px; height: 54px; border-radius: 18px; display: grid; place-items: center; background: #fff; box-shadow: 0 10px 30px rgba(37,99,235,0.08); font-size: 22px; }
.detail-title h1 { font-size: 28px; }
.meta-card { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 18px; min-height: 72px; }
.meta-card--ring { flex-direction: column; min-width: 110px; }
.ok-text { color: #16a34a; } .bad-text { color: #e11d48; } .warn-text { color: #d97706; }

.kpi-row { display: grid; grid-template-columns: 1fr 1fr 1fr 0.85fr 1.15fr; gap: 12px; margin: 16px 0; }
.kpi { padding: 16px 18px; border-radius: 22px; }
.kpi-label { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: #64748b; }
.kpi-value { margin: 10px 0 8px; font-size: 28px; font-weight: 800; }
.kpi-sub, .kpi p { margin: 0; color: #7b93b0; font-size: 12px; line-height: 1.45; }
.kpi--temp { background: #fff1f2; } .kpi--press { background: #eff6ff; } .kpi--hum { background: #f0f9ff; }
.kpi--alert { background: #fff1f2; }
.kpi--reason strong { display: block; margin: 8px 0; font-size: 14px; }

.panel { padding: 16px 18px 12px; border-radius: 24px; background: #fff; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.panel-head h3 { margin: 0; font-size: 16px; }
.panel-head span { color: #7b93b0; font-weight: 500; font-size: 12px; }
.legend { color: #64748b; font-size: 12px; }
.swatch { width: 18px; height: 3px; display: inline-block; margin: 0 6px 0 10px; border-radius: 99px; }
.swatch-actual { background: #f43f5e; } .swatch-expected { background: #3b82f6; }

table.raw { width: 100%; border-collapse: collapse; font-size: 12px; }
table.raw th, table.raw td { text-align: left; padding: 9px 8px; border-bottom: 1px solid #eef3f9; white-space: nowrap; }
table.raw th { color: #94a3b8; font-weight: 600; }

.stRadio { margin-bottom: 0 !important; }
div[data-testid="stRadio"] > label { display: none; }
div[role="radiogroup"] { justify-content: flex-end; background: #eff6ff; padding: 4px; border-radius: 999px; gap: 4px; }
div[role="radiogroup"] label {
  background: transparent !important; padding: 6px 10px !important; border-radius: 999px !important;
  font-weight: 700 !important; color: #64748b !important;
}
div[role="radiogroup"] label:has(input:checked) { background: #3b82f6 !important; color: #fff !important; }

/* Clean styling for Streamlit tabs */
div[data-testid="stTabs"] {
  background: #ffffff;
  border-radius: 24px;
  padding: 14px 18px;
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08);
}
button[data-baseweb="tab"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  color: #64748b !important;
  border-radius: 12px !important;
  padding: 8px 16px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #2563eb !important;
  background: #eff6ff !important;
}

div[data-testid="stPlotlyChart"] {
  background: #fff;
  border-radius: 0 0 24px 24px;
}

@media (max-width: 980px) {
  .hero, .station-grid, .kpi-row { grid-template-columns: 1fr; }
  .hero-visual { display: flex; flex-wrap: wrap; }
}
</style>
"""


def health_ring(value: int, tone: str, size: int = 54) -> str:
    colors = {"ok": "#22c55e", "warn": "#f59e0b", "bad": "#f43f5e"}
    stroke = 6
    radius = (size - stroke) / 2
    circ = 2 * math.pi * radius
    offset = circ * (1 - value / 100)
    color = colors.get(tone, "#22c55e")
    return (
        f'<div class="health-ring" style="width:{size}px;height:{size}px">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="#e8eef7" stroke-width="{stroke}" />'
        f'<circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" '
        f'transform="rotate(-90 {size/2} {size/2})" />'
        f'</svg>'
        f'<span>{value}%</span>'
        f'</div>'
    )


def sparkline() -> str:
    return (
        '<svg class="hero-spark" viewBox="0 0 280 110" fill="none" width="100%" height="120">'
        '<defs>'
        '<linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#60A5FA" stop-opacity="0.35" />'
        '<stop offset="100%" stop-color="#60A5FA" stop-opacity="0" />'
        '</linearGradient>'
        '</defs>'
        '<path d="M8 78 C 28 74, 40 62, 58 58 C 80 52, 96 70, 118 64 C 142 57, 158 36, 180 32 C 204 27, 220 48, 242 30 C 254 22, 266 18, 274 14 L 274 104 L 8 104 Z" fill="url(#sparkFill)" />'
        '<path d="M8 78 C 28 74, 40 62, 58 58 C 80 52, 96 70, 118 64 C 142 57, 158 36, 180 32 C 204 27, 220 48, 242 30 C 254 22, 266 18, 274 14" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" />'
        '<circle cx="242" cy="30" r="6" fill="#FB7185" />'
        '</svg>'
    )


def header_html(last_updated: str = LAST_UPDATED) -> str:
    return (
        '<div class="topbar">'
        '<div class="topbar-left">'
        '<a class="home-btn" href="?" target="_self" aria-label="Back to stations">⌂</a>'
        '<div class="brand">'
        '<div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#60A5FA,#2563EB);display:grid;place-items:center;color:white;font-size:16px">☁</div>'
        '<div>'
        '<div class="brand-name">SkyGuard AI</div>'
        '<div class="brand-sub">Powered by Nexora</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="topbar-right">'
        '<div class="status-pill"><span class="dot"></span> System Operational</div>'
        f'<div class="updated-pill">◷ Last Updated: {last_updated}</div>'
        '<div class="nexora">⬡ Nexora</div>'
        '</div>'
        '</div>'
    )


def station_status_class(status: str) -> str:
    return {"Normal": "ok-text", "Warning": "warn-text"}.get(status, "bad-text")


def humidity_label(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return str(rounded)
    return f"{value:.1f}"


def card_health(station: dict) -> str:
    return health_ring(station["sensorHealth"], health_tone(station["sensorHealth"]))


def card_badge(station: dict) -> str:
    return connectivity_class(station["connectivity"])
