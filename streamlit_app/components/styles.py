"""
Styles and CSS injection module for SkyGuard AI Streamlit application.
Replicates the visual fidelity of the provided user screenshots.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
/* Import Inter & JetBrains Mono Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
}

/* App Background */
.stApp {
    background-color: #f8fafc;
}

/* Hide Streamlit default header decoration and footer padding */
header[data-testid="stHeader"] {
    background-color: rgba(248, 250, 252, 0.85);
    backdrop-filter: blur(8px);
}
#MainMenu, footer, [data-testid="stDecoration"] {
    display: none !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1380px !important;
}

/* Top Navigation Bar */
.top-nav-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 12px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.nav-brand-group {
    display: flex;
    align-items: center;
    gap: 14px;
}
.nav-brand-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: #1e3a8a;
    line-height: 1.1;
}
.nav-brand-subtitle {
    font-size: 0.72rem;
    color: #64748b;
    font-weight: 600;
}
.nav-status-group {
    display: flex;
    align-items: center;
    gap: 20px;
}
.nav-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.nav-clock {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #475569;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Hero Banner Card */
.hero-banner {
    position: relative;
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 45%, #60a5fa 100%);
    border-radius: 20px;
    padding: 36px 44px;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.35);
    overflow: hidden;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.hero-content {
    max-width: 620px;
    z-index: 2;
}
.hero-tagline {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #bfdbfe;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 900;
    line-height: 1.15;
    margin-bottom: 10px;
    color: #ffffff;
}
.hero-desc {
    font-size: 0.95rem;
    line-height: 1.5;
    color: #e0e7ff;
}
.hero-right-card {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    z-index: 2;
}
.hero-alert-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(239, 68, 68, 0.92);
    color: #ffffff;
    font-size: 0.78rem;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}
.hero-checklist-card {
    background: rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.28);
    border-radius: 14px;
    padding: 10px 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.checklist-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    color: #ffffff;
}

/* Section Header */
.section-header-box {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}
.section-header-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}
.section-header-sub {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 2px;
}

/* Station Card (Page 1) */
.station-card-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
    margin-bottom: 16px;
    position: relative;
}
.station-card-box:hover {
    border-color: #93c5fd;
    box-shadow: 0 10px 20px -3px rgba(37, 99, 235, 0.12);
}

.card-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.pixel-station-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    color: #2563eb;
    background: #eff6ff;
    border: 2px solid #bfdbfe;
    border-radius: 12px;
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: -1px;
}
.station-title-group {
    display: flex;
    flex-direction: column;
}
.station-title-text {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
}
.station-sub-text {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
}

/* 3 Sensor Readings Row */
.sensors-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 18px;
}
.sensor-cell {
    display: flex;
    align-items: center;
    gap: 10px;
}
.sensor-cell-val {
    font-size: 0.95rem;
    font-weight: 800;
    color: #0f172a;
}
.sensor-cell-lbl {
    font-size: 0.7rem;
    color: #64748b;
    font-weight: 600;
}

/* Card Bottom Row */
.card-bottom-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid #f1f5f9;
    padding-top: 14px;
}

/* Circular Health Meter Gauge */
.health-ring-gauge {
    position: relative;
    width: 44px;
    height: 44px;
    display: inline-block;
}
.health-ring-gauge svg {
    transform: rotate(-90deg);
    width: 44px;
    height: 44px;
}
.health-ring-gauge circle {
    fill: none;
    stroke-width: 4;
}
.health-ring-gauge .bg-ring {
    stroke: #e2e8f0;
}
.health-ring-gauge .val-ring {
    stroke-linecap: round;
}
.health-ring-val {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.72rem;
    font-weight: 800;
    color: #0f172a;
}

/* Badges */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
}
.badge-online { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.badge-warning { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.badge-critical { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

/* Anomaly Badges */
.anom-type-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.anom-spike { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
.anom-rail { background: #fef2f2; color: #991b1b; border: 1px solid #f87171; }
.anom-drift { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.anom-frozen { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
.anom-front { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

.sev-badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 800;
    text-transform: uppercase;
}
.sev-critical { background: #dc2626; color: white; }
.sev-high { background: #ea580c; color: white; }
.sev-medium { background: #d97706; color: white; }
.sev-low { background: #0284c7; color: white; }

/* Station Detail Header Bar */
.detail-header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 16px 28px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.tower-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* 5 Metric Cards */
.metric-card-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.metric-card-anom {
    background: #fffcfc;
    border-color: #fca5a5;
}
.metric-card-top {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 8px;
}
.metric-card-val {
    font-size: 1.7rem;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
    margin-bottom: 12px;
}
.metric-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.72rem;
    color: #64748b;
    border-top: 1px solid #f1f5f9;
    padding-top: 8px;
}
.delta-badge {
    padding: 2px 7px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
}
.delta-bad { background: #fef2f2; color: #dc2626; }
.delta-good { background: #f0fdf4; color: #16a34a; }

/* Anomaly Status Card (Card 5) */
.anomaly-card-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    height: 100%;
}
.anomaly-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.anomaly-status-alert { background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; }
.anomaly-status-normal { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.anomaly-reason-box {
    font-size: 0.74rem;
    line-height: 1.45;
    color: #475569;
}

/* Breadcrumb Bar */
.breadcrumb-box {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #64748b;
    margin-bottom: 16px;
}
.breadcrumb-link {
    color: #2563eb;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
}

/* Table styling */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    text-align: left;
}
.custom-table th {
    background: #f8fafc;
    color: #64748b;
    font-weight: 700;
    padding: 10px 8px;
    border-bottom: 1px solid #e2e8f0;
}
.custom-table td {
    padding: 9px 8px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
}
.custom-table tr:hover td {
    background: #f0f7ff;
}

/* Streamlit Button Tweaks */
div.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    border: 1px solid #cbd5e1;
    transition: all 0.2s;
}
div.stButton > button:hover {
    border-color: #2563eb;
    color: #2563eb;
}
</style>
"""

def inject_custom_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
