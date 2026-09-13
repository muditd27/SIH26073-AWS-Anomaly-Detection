"""
SkyGuard AI — Powered by Nexora
5-Page Streamlit Application Entrypoint
- Page 1: Overview Summary Dashboard (? / no query param)
- Pages 2–5: Station Detail Work Pages (?station=AWS001..AWS004)
"""
from __future__ import annotations

import streamlit as st

from data import get_station, get_stations
from station_detail import render_station_detail
from stations_page import render_stations_page
from ui import header_html, inject_css

st.set_page_config(
    page_title="SkyGuard AI — Powered by Nexora",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(inject_css(), unsafe_allow_html=True)

# Station selected via query parameter (?station=AWS001)
station_id = st.query_params.get("station")
stations = get_stations()
station = get_station(station_id) if station_id else None

last_updated = stations[0]["lastUpdated"] if stations and "lastUpdated" in stations[0] else "14:32:08"
st.markdown(header_html(last_updated), unsafe_allow_html=True)

if station_id and not station:
    st.query_params.clear()
    st.markdown(render_stations_page(stations), unsafe_allow_html=True)
elif station:
    render_station_detail(station)
else:
    st.markdown(render_stations_page(stations), unsafe_allow_html=True)
