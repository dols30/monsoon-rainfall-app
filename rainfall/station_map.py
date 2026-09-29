"""Offline station picker with a geographic outline of Nepal."""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v2 as components


ASSETS = Path(__file__).resolve().parents[1] / "assets"

def map_forecast(saved, location, fingerprint):
    """The saved forecast in the shape the map draws, or None once the station or inputs have changed."""
    if not saved or saved.get("location") != location or saved.get("inputs") != fingerprint:
        return None
    return {"location": location, "rain": bool(saved["result"].rain), "probability": float(saved["result"].probability)}


def render_station_map(locations: tuple[str, ...], forecast: dict | None = None):
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
            "forecast": forecast,
        },
        key="nepal_map",
        on_station_change=select_station,
    )
