"""Offline station picker with a geographic outline of Nepal."""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v2 as components


ASSETS = Path(__file__).resolve().parents[1] / "assets"

def render_station_map(locations: tuple[str, ...]):
    if not locations:
        return
    if st.session_state.get("location") not in locations:
        st.session_state["location"] = "Kathmandu" if "Kathmandu" in locations else locations[0]
    map_data = json.loads((ASSETS / "nepal-map.json").read_text())

    station_picker = components.component(
        "nepal_station_picker",
        html=(ASSETS / "station-map.html").read_text(),
        css=(ASSETS / "station-map.css").read_text(),
        js=(ASSETS / "station-map.js").read_text(),
    )

    def select_station():
        selected = st.session_state["nepal_map"].get("station")
        if selected in locations:
            st.session_state["location"] = selected

    station_picker(
        data={
            "boundary": map_data["boundary"],
            "provinces": map_data["provinces"],
            "stations": [station for station in map_data["stations"] if station["name"] in locations],
            "selected": st.session_state["location"],
        },
        key="nepal_map",
        on_station_change=select_station,
    )
