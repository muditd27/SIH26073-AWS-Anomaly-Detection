"""
SkyGuard AI — Powered by Nexora
5-Page Streamlit Single Page Application
Pages:
- Page 1: Overview Summary Dashboard (#/stations)
- Pages 2-5: Station Detail Work Pages (AWS001, AWS002, AWS003, AWS004)
"""

import sys
from pathlib import Path
import streamlit as st

# Setup python path to include streamlit_app and backend
app_file = Path(__file__).resolve()
app_dir = app_file.parent
repo_root = app_dir.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from data_provider import (
    get_stations_summary,
    get_station_detail,
    get_station_trends,
    get_station_raw_data,
    get_station_anomalies,
    get_network_anomalies,
    run_step_simulation,
    resolve_display_id,
)
from components.styles import inject_custom_css
from components.views import (
    render_top_navbar,
    render_overview_page,
    render_station_detail_page,
)


def main():
    # Page configuration
    st.set_page_config(
        page_title="SkyGuard AI — Powered by Nexora",
        page_icon="🌤️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom CSS
    inject_custom_css()

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "overview"
    if "current_station" not in st.session_state:
        st.session_state.current_station = "AWS001"
    if "time_range" not in st.session_state:
        st.session_state.time_range = "3M"
    if "last_updated" not in st.session_state:
        st.session_state.last_updated = "14:32:08"

    # -------------------------------------------------------------
    # Sidebar Controls & Quick Station Switcher
    # -------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5">
                    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path>
                </svg>
                <div>
                    <strong style="font-size:1.1rem; color:#1e3a8a;">SkyGuard AI</strong><br>
                    <span style="font-size:0.75rem; color:#64748b;">Powered by Nexora</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 🧭 Navigation")
        nav_options = [
            "📊 All Stations Overview",
            "01 AWS001 (Station 01)",
            "02 AWS002 (Station 02)",
            "03 AWS003 (Station 03)",
            "04 AWS004 (Station 04)",
        ]

        curr_idx = 0
        if st.session_state.page == "detail":
            if st.session_state.current_station == "AWS001": curr_idx = 1
            elif st.session_state.current_station == "AWS002": curr_idx = 2
            elif st.session_state.current_station == "AWS003": curr_idx = 3
            elif st.session_state.current_station == "AWS004": curr_idx = 4

        selected_nav = st.radio(
            "Select Page",
            options=nav_options,
            index=curr_idx,
            label_visibility="collapsed",
            key="sidebar_nav_radio",
        )

        if selected_nav == "📊 All Stations Overview":
            if st.session_state.page != "overview":
                st.session_state.page = "overview"
                st.rerun()
        else:
            st_code = selected_nav.split(" ")[1]
            if st.session_state.page != "detail" or st.session_state.current_station != st_code:
                st.session_state.page = "detail"
                st.session_state.current_station = st_code
                st.rerun()

        st.markdown("<hr style='margin: 16px 0; border: none; border-bottom: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("### ⚡ Simulation Engine")
        st.caption("Trigger a live 1-batch ingestion step through the 3-Tier ML pipeline (Isolation Forest + XGBoost Regressors + XGBoost Classifier).")

        if st.button("⚡ Run Simulation Step", use_container_width=True, type="primary"):
            with st.spinner("Processing live 4-station batch through Complete Loop..."):
                res = run_step_simulation()
                if res.get("status") == "success":
                    st.success("✅ Batch processed & database updated!")
                    st.rerun()
                else:
                    st.error(f"Simulation error: {res.get('message')}")

        st.markdown("<hr style='margin: 16px 0; border: none; border-bottom: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:0.75rem; color:#64748b; line-height:1.4;">
                <strong>Sensors Monitored:</strong><br>
                • Temperature (°C)<br>
                • Pressure (hPa)<br>
                • Relative Humidity (%)<br><br>
                <em>Wind and Weather conditions strictly removed per problem statement.</em>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------
    # Main Application Content
    # -------------------------------------------------------------

    # 1. Top Navbar
    render_top_navbar(st.session_state.last_updated)

    # 2. Render Selected Page
    if st.session_state.page == "overview":
        stations = get_stations_summary()
        if stations and len(stations) > 0:
            st.session_state.last_updated = stations[0]["last_updated"]
        network_anomalies = get_network_anomalies()
        render_overview_page(stations, network_anomalies)

    else:
        station_id = st.session_state.current_station
        summary = get_station_detail(station_id)
        trends = get_station_trends(station_id, st.session_state.time_range)
        raw_data = get_station_raw_data(station_id)
        anomalies = get_station_anomalies(station_id)
        render_station_detail_page(station_id, summary, trends, raw_data, anomalies)


if __name__ == "__main__":
    main()
