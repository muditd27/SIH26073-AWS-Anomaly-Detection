"""
View components for SkyGuard AI Streamlit application:
1. Top Navbar
2. Page 1: Overview Summary Dashboard (matching Image 1)
3. Pages 2-5: Station Detail Work Pages (matching Image 2)
"""

import streamlit as st
from typing import List, Dict, Any
from .charts import create_dual_line_chart


def get_health_gauge_svg(score: int) -> str:
    """Generates an SVG circular health ring gauge matching the user screenshots."""
    color = "#10b981"
    if score < 70:
        color = "#ef4444"
    elif score < 85:
        color = "#f59e0b"

    circumference = 2 * 3.14159 * 18
    offset = circumference - (score / 100.0) * circumference

    return f"""
    <div class="health-ring-gauge">
      <svg viewBox="0 0 44 44">
        <circle class="bg-ring" cx="22" cy="22" r="18" />
        <circle class="val-ring" cx="22" cy="22" r="18" stroke="{color}" stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}" />
      </svg>
      <span class="health-ring-val">{score}%</span>
    </div>
    """


def get_anomaly_badge_html(anom_type: str) -> str:
    """Returns styled HTML pill for anomaly classification."""
    t = str(anom_type or "NORMAL").upper()
    if "SPIKE" in t:
        return '<span class="anom-type-badge anom-spike">SENSOR SPIKE</span>'
    if "RAIL" in t or "BOUND" in t:
        return '<span class="anom-type-badge anom-rail">OUT OF BOUNDS</span>'
    if "DRIFT" in t:
        return '<span class="anom-type-badge anom-drift">SENSOR DRIFT</span>'
    if "FROZEN" in t:
        return '<span class="anom-type-badge anom-frozen">FROZEN SENSOR</span>'
    if "FRONT" in t or "WEATHER" in t:
        return '<span class="anom-type-badge anom-front">WEATHER FRONT</span>'
    return f'<span class="anom-type-badge anom-spike">{t}</span>'


def get_severity_badge_html(sev: str) -> str:
    """Returns styled HTML pill for anomaly severity."""
    s = str(sev or "MEDIUM").upper()
    if s == "CRITICAL":
        return '<span class="sev-badge sev-critical">CRITICAL</span>'
    if s == "HIGH":
        return '<span class="sev-badge sev-high">HIGH</span>'
    if s == "MEDIUM":
        return '<span class="sev-badge sev-medium">MEDIUM</span>'
    return '<span class="sev-badge sev-low">LOW</span>'


def render_top_navbar(last_updated: str = "14:32:08"):
    """Renders the top navigation header bar."""
    c1, c2, c3, c4 = st.columns([4, 2, 2, 2], vertical_alignment="center")

    with c1:
        # Brand & Cloud Logo
        st.markdown(
            f"""
            <div class="nav-brand-group">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path>
                    <polyline points="12 11 12 15 14 13"></polyline>
                </svg>
                <div>
                    <div class="nav-brand-title">SkyGuard AI</div>
                    <div class="nav-brand-subtitle">Powered by Nexora</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div style="display:flex; justify-content:center;">
                <span class="nav-status-pill">● System Operational</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="nav-clock" style="justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>Last Updated: {last_updated}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            """
            <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2">
                    <circle cx="18" cy="5" r="3"></circle>
                    <circle cx="6" cy="12" r="3"></circle>
                    <circle cx="18" cy="19" r="3"></circle>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                </svg>
                <span style="font-size:1.15rem; font-weight:800; color:#1e293b;">Nexora</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-bottom: 1px solid #e2e8f0;'>", unsafe_allow_html=True)


def render_overview_page(stations: List[Dict[str, Any]], network_anomalies: List[Dict[str, Any]]):
    """Renders Page 1: Overview Summary Dashboard (Image 1)."""
    # 1. Hero Banner Card
    st.markdown(
        """
        <div class="hero-banner">
          <div class="hero-content">
            <div class="hero-tagline">AI-Powered Weather Monitoring</div>
            <h1 class="hero-title">Welcome to SkyGuard AI</h1>
            <p class="hero-desc">
              Monitor your AWS network in real-time with AI-driven anomaly detection.
              Select a station below to view detailed insights, sensor readings, and ML predictions.
            </p>
          </div>
          <div class="hero-right-card">
            <div class="hero-alert-badge">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              <span>Anomaly Detected</span>
            </div>
            <div class="hero-checklist-card">
              <div class="checklist-row">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Detect</span>
              </div>
              <div class="checklist-row">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Analyze</span>
              </div>
              <div class="checklist-row">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Report</span>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Section Header
    st.markdown(
        """
        <div class="section-header-box">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#2563eb" stroke="#2563eb" stroke-width="1.5">
                <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8zm0 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z" fill="#2563eb"></path>
            </svg>
            <div>
                <h2 class="section-header-title">Select a Weather Station</h2>
                <div class="section-header-sub">Choose a station to view live data, AI predictions, and anomaly insights.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. 2x2 Station Cards Grid
    c_left, c_right = st.columns(2, gap="medium")

    for idx, st_data in enumerate(stations):
        col = c_left if idx % 2 == 0 else c_right
        with col:
            badge_cls = "badge-online"
            if st_data["status_badge"] == "Warning":
                badge_cls = "badge-warning"
            elif st_data["status_badge"] == "Critical":
                badge_cls = "badge-critical"

            gauge_svg = get_health_gauge_svg(st_data["sensor_health"])

            anom_icon_svg = (
                '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
                if st_data["anomaly_status"] == "Normal"
                else (
                    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
                    if st_data["anomaly_status"] == "Possible Anomaly"
                    else '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
                )
            )

            # Render styled card container
            st.markdown(
                f"""
                <div class="station-card-box">
                    <div class="card-top-row">
                        <div style="display:flex; align-items:center; gap:14px;">
                            <div class="pixel-station-number">{st_data["number"]}</div>
                            <div class="station-title-group">
                                <div class="station-title-text">
                                    {st_data["display_id"]}
                                    <span class="badge-pill {badge_cls}">● {st_data["status_badge"]}</span>
                                </div>
                                <div class="station-sub-text">{st_data["station_name"]}</div>
                            </div>
                        </div>
                    </div>

                    <div class="sensors-grid-3">
                        <div class="sensor-cell">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.2"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"></path></svg>
                            <div>
                                <div class="sensor-cell-val">{st_data["temperature"]} °C</div>
                                <div class="sensor-cell-lbl">Temperature</div>
                            </div>
                        </div>
                        <div class="sensor-cell">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                            <div>
                                <div class="sensor-cell-val">{st_data["pressure"]} hPa</div>
                                <div class="sensor-cell-lbl">Pressure</div>
                            </div>
                        </div>
                        <div class="sensor-cell">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>
                            <div>
                                <div class="sensor-cell-val">{st_data["relative_humidity"]} %</div>
                                <div class="sensor-cell-lbl">Rel. Humidity</div>
                            </div>
                        </div>
                    </div>

                    <div class="card-bottom-row">
                        <div style="display:flex; align-items:center; gap:10px;">
                            {gauge_svg}
                            <span style="font-size:0.75rem; color:#64748b; font-weight:600;">Sensor Health</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:6px;">
                            {anom_icon_svg}
                            <div>
                                <div style="font-size:0.8rem; font-weight:700; color:#0f172a;">{st_data["anomaly_status"]}</div>
                                <div style="font-size:0.68rem; color:#64748b;">Anomaly Status</div>
                            </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:6px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            <div>
                                <div style="font-size:0.8rem; font-weight:700; color:#0f172a;">{st_data["last_updated"]}</div>
                                <div style="font-size:0.68rem; color:#64748b;">Last Updated</div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Button to open this station's detail page
            if st.button(
                f"Open Detailed Work Page for {st_data['display_id']} ➔",
                key=f"btn_open_{st_data['display_id']}",
                use_container_width=True,
            ):
                st.session_state.current_station = st_data["display_id"]
                st.session_state.page = "detail"
                st.rerun()

    # 4. Live Network Anomaly Feed
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="station-card-box" style="padding: 20px 24px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <span style="font-size:1.15rem; font-weight:800; color:#0f172a;">Live Network Anomaly Feed</span>
                    <span class="anom-type-badge anom-spike">{len(network_anomalies)} Events</span>
                </div>
                <span style="font-size:0.75rem; color:#64748b; font-weight:600;">Automated 3-Tier Pipeline</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Render table rows
    table_html = """
    <table class="custom-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Station</th>
                <th>Detected At</th>
                <th>Anomaly Pattern</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Diagnostics / SHAP Explanation</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
    """
    for a in network_anomalies[:8]:
        st_id = a.get("display_id", a.get("station_id", "AWS001"))
        type_badge = get_anomaly_badge_html(a.get("anomaly_type", ""))
        sev_badge = get_severity_badge_html(a.get("severity", "MEDIUM"))
        table_html += f"""
            <tr>
                <td style="font-weight:700; color:#64748b;">{a.get('index', 1)}</td>
                <td style="font-weight:800; color:#2563eb;">{st_id}</td>
                <td style="font-family:monospace; font-size:0.75rem;">{a.get('detected_at', '')}</td>
                <td>{type_badge}</td>
                <td>{sev_badge}</td>
                <td style="font-weight:700;">{a.get('confidence', 88)}%</td>
                <td style="max-width:320px;">{a.get('explanation', '')}</td>
                <td style="color:#64748b; font-size:0.72rem;">{a.get('recommended_action', 'Inspect unit')}</td>
            </tr>
        """
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)


def render_station_detail_page(
    station_id: str,
    summary: Dict[str, Any],
    trends: Dict[str, Any],
    raw_data: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
):
    """Renders Pages 2-5: Detailed Work Page for Station (Image 2)."""
    # 1. Breadcrumb Bar with Home navigation
    b_col1, b_col2 = st.columns([8, 2], vertical_alignment="center")
    with b_col1:
        st.markdown(
            f"""
            <div class="breadcrumb-box">
                <span style="color:#2563eb; font-weight:700;">SkyGuard AI</span> &gt;
                <span style="color:#2563eb; font-weight:700;">Stations</span> &gt;
                <strong style="color:#0f172a;">{station_id}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b_col2:
        if st.button("⬅ Back to All Stations", key="btn_back_home", use_container_width=True):
            st.session_state.page = "overview"
            st.rerun()

    # 2. Station Header Row (Image 2)
    gauge_svg = get_health_gauge_svg(summary["sensor_health"])
    st.markdown(
        f"""
        <div class="detail-header-bar">
            <div style="display:flex; align-items:center; gap:16px;">
                <div class="tower-icon-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"></path>
                        <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"></path>
                        <circle cx="12" cy="12" r="2"></circle>
                        <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"></path>
                        <path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"></path>
                    </svg>
                </div>
                <div>
                    <div style="font-size:1.6rem; font-weight:800; color:#0f172a; display:flex; align-items:center; gap:10px;">
                        {summary["display_id"]}
                        <span class="badge-pill badge-online">● {summary["status_badge"]}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#64748b; font-weight:600;">{summary["station_name"]}</div>
                </div>
            </div>

            <div style="display:flex; align-items:center; gap:32px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <div>
                        <div style="font-size:0.7rem; color:#64748b; font-weight:600;">Last Recorded</div>
                        <div style="font-size:0.88rem; font-weight:700; color:#0f172a;">{summary["last_recorded"]}</div>
                    </div>
                </div>

                <div style="display:flex; align-items:center; gap:10px;">
                    {gauge_svg}
                    <div style="font-size:0.8rem; font-weight:700; color:#475569;">Sensor Health</div>
                </div>

                <div style="display:flex; align-items:center; gap:8px;">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="#fbbf24" stroke="#f59e0b" stroke-width="1.8">
                        <circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path>
                    </svg>
                    <div>
                        <div style="font-size:0.88rem; font-weight:700; color:#0f172a;">{summary["station_status"]}</div>
                        <div style="font-size:0.7rem; color:#64748b; font-weight:600;">Station Status</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Top 5 Metric Cards Row
    m1, m2, m3, m4, m5 = st.columns(5, gap="small")

    # Card 1: Temperature
    t_data = summary["temperature"]
    t_delta_cls = "delta-bad" if t_data["is_anomalous"] else "delta-good"
    t_card_cls = "metric-card-box metric-card-anom" if t_data["is_anomalous"] else "metric-card-box"
    with m1:
        st.markdown(
            f"""
            <div class="{t_card_cls}">
                <div class="metric-card-top">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"></path></svg>
                    <span>Temperature</span>
                </div>
                <div class="metric-card-val">{t_data["actual"]} °C</div>
                <div class="metric-card-footer">
                    <span>Expected: {t_data["expected"]} °C</span>
                    <span class="delta-badge {t_delta_cls}">Δ: {t_data["delta"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 2: Pressure
    p_data = summary["pressure"]
    p_delta_cls = "delta-bad" if p_data["is_anomalous"] else "delta-good"
    with m2:
        st.markdown(
            f"""
            <div class="metric-card-box">
                <div class="metric-card-top">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                    <span>Pressure</span>
                </div>
                <div class="metric-card-val">{p_data["actual"]} hPa</div>
                <div class="metric-card-footer">
                    <span>Expected: {p_data["expected"]} hPa</span>
                    <span class="delta-badge {p_delta_cls}">Δ: {p_data["delta"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 3: Relative Humidity
    rh_data = summary["humidity"]
    rh_delta_cls = "delta-bad" if rh_data["is_anomalous"] else "delta-good"
    with m3:
        st.markdown(
            f"""
            <div class="metric-card-box">
                <div class="metric-card-top">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.5"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>
                    <span>Relative Humidity</span>
                </div>
                <div class="metric-card-val">{rh_data["actual"]} %</div>
                <div class="metric-card-footer">
                    <span>Expected: {rh_data["expected"]} %</span>
                    <span class="delta-badge {rh_delta_cls}">Δ: {rh_data["delta"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 4: Anomaly Score
    score_data = summary["anomaly_score"]
    with m4:
        st.markdown(
            f"""
            <div class="metric-card-box">
                <div class="metric-card-top">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    <span>Anomaly Score</span>
                </div>
                <div class="metric-card-val">{score_data["score"]:.2f}</div>
                <div class="metric-card-footer">
                    <span>Confidence</span>
                    <strong style="color:#0f172a;">{score_data["confidence"]}%</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 5: Anomaly Status & SHAP Plain-English Reason
    anom_status = summary["anomaly_status"]
    anom_pill_cls = "anomaly-status-alert" if anom_status["is_anomaly"] else "anomaly-status-normal"
    anom_pill_text = "▲ ANOMALY DETECTED" if anom_status["is_anomaly"] else "✓ NORMAL STATUS"
    with m5:
        st.markdown(
            f"""
            <div class="anomaly-card-box">
                <div style="font-size:0.75rem; color:#64748b; font-weight:700; margin-bottom:6px;">Anomaly Status</div>
                <div class="anomaly-status-badge {anom_pill_cls}">{anom_pill_text}</div>
                <div class="anomaly-reason-box">
                    <strong>Reason:</strong> {anom_status["reason"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 4. Main Split Content: Trends on Left (60%) | Dual Tabs on Right (40%)
    col_trends, col_tables = st.columns([6, 4], gap="medium")

    with col_trends:
        # Trends Header & Range Selector
        th_1, th_2 = st.columns([7, 3], vertical_alignment="center")
        with th_1:
            st.markdown(
                """
                <div style="display:flex; align-items:center; gap:8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                    <span style="font-size:1.15rem; font-weight:800; color:#0f172a;">Sensor Trends</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with th_2:
            current_range = st.radio(
                "Time Range",
                options=["3M", "1M", "7D"],
                index=0 if st.session_state.get("time_range", "3M") == "3M" else (1 if st.session_state.get("time_range") == "1M" else 2),
                horizontal=True,
                label_visibility="collapsed",
                key="time_range_radio",
            )
            if current_range != st.session_state.get("time_range", "3M"):
                st.session_state.time_range = current_range
                st.rerun()

        # 3 Synchronized Trend Charts (Temperature, Pressure, Relative Humidity)
        timestamps = trends.get("timestamps", [])
        labels = trends.get("labels", [])

        # Chart 1: Temperature (°C)
        t_chart_data = trends.get("temperature", {})
        fig_temp = create_dual_line_chart(
            title="Temperature (°C)",
            unit="°C",
            timestamps=timestamps,
            labels=labels,
            actual=t_chart_data.get("actual", []),
            expected=t_chart_data.get("expected", []),
            actual_color="#ef4444",
            expected_color="#0284c7",
            height=210,
        )
        st.plotly_chart(fig_temp, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

        # Chart 2: Pressure (hPa)
        p_chart_data = trends.get("pressure", {})
        fig_pres = create_dual_line_chart(
            title="Pressure (hPa)",
            unit="hPa",
            timestamps=timestamps,
            labels=labels,
            actual=p_chart_data.get("actual", []),
            expected=p_chart_data.get("expected", []),
            actual_color="#ef4444",
            expected_color="#0284c7",
            height=210,
        )
        st.plotly_chart(fig_pres, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

        # Chart 3: Relative Humidity (%)
        rh_chart_data = trends.get("humidity", {})
        fig_rh = create_dual_line_chart(
            title="Relative Humidity (%)",
            unit="%",
            timestamps=timestamps,
            labels=labels,
            actual=rh_chart_data.get("actual", []),
            expected=rh_chart_data.get("expected", []),
            actual_color="#ef4444",
            expected_color="#0284c7",
            height=210,
        )
        st.plotly_chart(fig_rh, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

    with col_tables:
        # Dual Tabs: Anomaly Log & Raw Telemetry
        tab_anom, tab_raw = st.tabs([f"⚠️ Anomaly Log ({len(anomalies)})", "📊 Raw Telemetry"])

        with tab_anom:
            st.markdown(
                f"""
                <div style="font-size:0.85rem; font-weight:700; color:#64748b; margin-bottom:10px;">
                    Recorded Anomaly Events for {summary['display_id']}
                </div>
                """,
                unsafe_allow_html=True,
            )
            anom_table_html = """
            <div style="max-height: 640px; overflow-y: auto;">
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Detected At</th>
                        <th>Type</th>
                        <th>Severity</th>
                        <th>Conf.</th>
                        <th>Diagnostics &amp; Recommended Action</th>
                    </tr>
                </thead>
                <tbody>
            """
            for a in anomalies:
                type_badge = get_anomaly_badge_html(a.get("anomaly_type", ""))
                sev_badge = get_severity_badge_html(a.get("severity", "MEDIUM"))
                anom_table_html += f"""
                    <tr>
                        <td style="font-weight:700; color:#64748b;">{a.get('index', 1)}</td>
                        <td style="font-family:monospace; font-size:0.72rem; white-space:nowrap;">{a.get('detected_at', '')}</td>
                        <td>{type_badge}</td>
                        <td>{sev_badge}</td>
                        <td style="font-weight:700;">{a.get('confidence', 88)}%</td>
                        <td>
                            <div style="font-weight:600; color:#0f172a; margin-bottom:2px;">{a.get('explanation', '')}</div>
                            <div style="font-size:0.7rem; color:#64748b;"><strong style="color:#2563eb;">Action:</strong> {a.get('recommended_action', 'Inspect unit')}</div>
                        </td>
                    </tr>
                """
            anom_table_html += "</tbody></table></div>"
            st.markdown(anom_table_html, unsafe_allow_html=True)

        with tab_raw:
            st.markdown(
                f"""
                <div style="font-size:0.85rem; font-weight:700; color:#64748b; margin-bottom:10px;">
                    Recent Telemetry (Last 4 Hours) — Strict 3 Sensors
                </div>
                """,
                unsafe_allow_html=True,
            )
            raw_table_html = """
            <div style="max-height: 640px; overflow-y: auto;">
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Timestamp</th>
                        <th>Temp (°C)</th>
                        <th>Pressure (hPa)</th>
                        <th>Rel. Humidity (%)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for r in raw_data:
                raw_table_html += f"""
                    <tr>
                        <td style="font-weight:700; color:#64748b;">{r['index']}</td>
                        <td style="font-family:monospace; font-size:0.75rem;">{r['timestamp']}</td>
                        <td style="font-weight:700;">{r['temperature']}</td>
                        <td>{r['pressure']}</td>
                        <td>{r['humidity']}</td>
                    </tr>
                """
            raw_table_html += "</tbody></table></div>"
            st.markdown(raw_table_html, unsafe_allow_html=True)

    # Footer
    st.markdown("<hr style='margin: 32px 0 16px 0; border: none; border-bottom: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    f1, f2 = st.columns([6, 6])
    with f1:
        st.markdown(
            f"<div style='font-size:0.8rem; color:#64748b;'>SkyGuard AI &gt; Stations &gt; <strong style='color:#0f172a;'>{station_id}</strong></div>",
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            "<div style='text-align:right; font-size:0.8rem; color:#64748b; font-weight:600;'>⚡ Smarter Monitoring, Safer Tomorrow.</div>",
            unsafe_allow_html=True,
        )
