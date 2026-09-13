from __future__ import annotations

import streamlit as st

from data import get_station
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
st.markdown(header_html(), unsafe_allow_html=True)

station_id = st.query_params.get("station")
station = get_station(station_id)

if station_id and not station:
    st.query_params.clear()
    st.markdown(render_stations_page(), unsafe_allow_html=True)
elif station:
    render_station_detail(station)
else:
    st.markdown(render_stations_page(), unsafe_allow_html=True)
