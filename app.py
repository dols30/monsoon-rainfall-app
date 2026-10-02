import base64
from datetime import date, datetime, timedelta
from html import escape
import json
import logging
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from rainfall import weather
from rainfall.explain import top_drivers
from rainfall.model import load_pipeline, predict, trained_locations
from rainfall.observations import ATMOSPHERE, FIELDS, MOISTURE, TEMPERATURE, WIND, build_features
from rainfall.station_map import map_forecast, render_station_map


ROOT = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("RAINFALL_MODEL_PATH", str(ROOT / "Nepal_Rainfall_XGBoost_Model.pkl")))
TODAY = datetime.now(ZoneInfo("Asia/Kathmandu")).date()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Monsoon: Nepal rainfall forecasting", page_icon="🌦", layout="wide", initial_sidebar_state="collapsed")
st.html(f"<style>{(ROOT / 'assets' / 'style.css').read_text()}</style>")


@st.cache_resource
def get_model(path: str, modified_at: int):
    pipeline = load_pipeline(Path(path))
    return pipeline, trained_locations(pipeline)


def reset_observations():
    for field in FIELDS:
        st.session_state[field.name] = field.default
    st.session_state["observed_on"] = TODAY
    st.session_state.pop("forecast", None)


def fill_from_open_meteo():
    location, day = st.session_state.get("location"), st.session_state.get("observed_on", TODAY)
    try:
        values = weather.fetch_day(location, day)
    except weather.WeatherUnavailable as error:
        st.session_state["autofill_status"] = ("error", str(error))
        return
    st.session_state.update(values)
    st.session_state.pop("forecast", None)
    st.session_state["autofill_status"] = ("ok", f"Filled from Open-Meteo for {location} on {day:%d %b %Y}. Check the values, then generate the forecast.")


def render_fields(fields):
    columns = st.columns(2, gap="large")
    for index, field in enumerate(fields):
        with columns[index % 2]:
            st.number_input(
                field.label, min_value=field.minimum, max_value=field.maximum,
                value=field.default, step=field.step, key=field.name,
                format="%.0f" if field.step == 1 else "%.1f",
            )


def render_forecast(saved, observed_on, location):
    forecast_on = observed_on + timedelta(days=1)
    loc_display = escape(location) if location else "Nepal"
    if saved:
        forecast = saved["result"]
        percent = forecast.probability * 100
        title = "Rain expected" if forecast.rain else "Rain unlikely"
        icon_name = "rain" if forecast.rain else "sun"
        content = f"""
            <div class="result-heading"><h3>{title}</h3>{asset_icon(icon_name)}</div>
            <div class="probability">{percent:.1f}<span>%</span></div>
            <p class="probability-label">Chance of rain</p>
            <div class="probability-track" role="meter" aria-label="Probability of rain"
                 aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent:.1f}">
                <div style="width:{percent:.3f}%"></div>
            </div>
            <div class="scale"><span>0%</span><span>100%</span></div>

        """
    else:
        content = f"""
            <div class="empty-result">{asset_icon('cloud')}<h3>No forecast yet</h3>
            </div>
        """
    backdrop = ROOT / "assets" / "himalayan-sky.webp"
    scenery = ""
    if backdrop.exists():
        encoded = base64.b64encode(backdrop.read_bytes()).decode("ascii")
        scenery = f'<img class="forecast-landscape" src="data:image/webp;base64,{encoded}" alt="" />'
    st.html(f"""
        <section class="forecast-card" id="forecast-card" aria-live="polite">
            <div class="forecast-place"><span>Next-day forecast</span><h2>{loc_display}</h2>
                <p>{forecast_on:%A, %d %B %Y}</p></div>
            {scenery}
            <div class="forecast-result">{content}</div>
            <div class="forecast-foot"><span>Rainfall threshold</span><strong>Above 1 mm</strong></div>
        </section>
    """)


def asset_icon(name):
    encoded = base64.b64encode((ROOT / "assets" / f"{name}.svg").read_bytes()).decode("ascii")
    return f'<img class="weather-symbol" src="data:image/svg+xml;base64,{encoded}" alt="" />'


def render_navigation():
    st.html(f"""
        <header class="site-header">
            <a class="brand" href="#top">{asset_icon('cloud')}<span>Monsoon</span></a>
            <nav aria-label="Main navigation"><a class="nav-active" href="#observations">Forecast</a>
            <a href="#stations">Stations</a></nav>

        </header>
    """)


def main():
    with st.container(key="masthead"):
        render_navigation()
    pipeline, locations, model_error = None, (), None
    model_version = None
    try:
        model_version = (str(MODEL_PATH), MODEL_PATH.stat().st_mtime_ns)
        pipeline, locations = get_model(*model_version)
    except FileNotFoundError:
        model_error = "The saved model is missing. Place Nepal_Rainfall_XGBoost_Model.pkl beside app.py."
    except Exception:
        logger.exception("Could not load rainfall pipeline")
        model_error = "The model could not be loaded. Check that it is the full pipeline and that package versions match its training environment."

    selected = st.session_state.get("location") or ("Kathmandu" if "Kathmandu" in locations else "Nepal")
    selected_date = st.session_state.get("observed_on", TODAY)
    st.html("""
        <header class="page-heading" id="top"><h1>Rainfall forecast</h1>
        </header>
    """)

    # Station network
    map_result = None
    if st.session_state.get("forecast"):
        try:
            current = build_features(selected_date, selected, {field.name: st.session_state[field.name] for field in FIELDS})
            map_result = map_forecast(st.session_state["forecast"], selected, current.to_json())
        except (KeyError, ValueError):
            pass

    if model_error:
        st.warning(model_error)

    inputs, output = st.columns([1.45, 1], gap="large")
    with inputs:
        st.html('<div id="observations" style="scroll-margin-top: 80px;"></div>')
        with st.container(border=False, key="observations"):
            st.html('<div class="section-heading"><h2>Weather observations</h2></div>')
            station_col, date_col = st.columns(2, gap="large")
            with station_col:
                location = st.selectbox(
                    "Weather station", locations,
                    index=locations.index("Kathmandu") if "Kathmandu" in locations else (0 if locations else None),
                    placeholder="No trained stations available", disabled=not locations, key="location",
                )
            with date_col:
                observed_on = st.date_input("Observation date", value=TODAY, min_value=date(2010, 1, 1), max_value=TODAY, key="observed_on")
            st.button("Fill from Open-Meteo", key="autofill", on_click=fill_from_open_meteo, disabled=not locations)
            status = st.session_state.pop("autofill_status", None)
            if status:
                (st.success if status[0] == "ok" else st.error)(status[1])
            with st.container():
                temp_tab, moisture_tab, wind_tab, air_tab = st.tabs(["Temperature", "Moisture", "Wind", "Pressure"])
                with temp_tab:
                    render_fields(TEMPERATURE)
                with moisture_tab:
                    render_fields(MOISTURE)
                with wind_tab:
                    render_fields(WIND)
                with air_tab:
                    render_fields(ATMOSPHERE)
            values = {field.name: st.session_state[field.name] for field in FIELDS}
            features, input_error = None, None
            if location:
                try:
                    features = build_features(observed_on, location, values)
                except ValueError as exc:
                    input_error = str(exc)
                    st.error(input_error)
            action, reset = st.columns([2.5, 1])
            with action:
                submitted = st.button("Generate forecast", key="generate", type="primary", width="stretch", disabled=pipeline is None or features is None)
            with reset:
                st.button("Reset values", key="reset", on_click=reset_observations, width="stretch")

        with st.expander("View model inputs"):
            if features is not None:
                st.dataframe(features.T.rename(columns={0: "Value"}).astype(str), width="stretch", height=310)
            else:
                st.caption(input_error or "Connect a model to select a trained station.")

    fingerprint = features.to_json() if features is not None else None
    if submitted:
        st.session_state.pop("forecast", None)
        try:
            with st.spinner("Calculating forecast…"):
                result = predict(pipeline, features)
            st.session_state["forecast"] = {"result": result, "inputs": fingerprint, "model_version": model_version, "location": location}
        except Exception:
            logger.exception("Rainfall prediction failed")
            with output:
                st.error("Could not generate a forecast. Check the model and its input format, then try again.")
        else:
            st.rerun()  # redraw the map with the new result

    saved = st.session_state.get("forecast")
    changed = saved is not None and (saved["inputs"] != fingerprint or saved["model_version"] != model_version)
    with output:
        if changed:
            st.info("Observations changed or the model was replaced. Generate a new forecast.")
        render_forecast(None if changed else saved, observed_on, location)
        if saved and not changed:
            report = {
                "location": location, "observed_on": observed_on.isoformat(),
                "forecast_for": (observed_on + timedelta(days=1)).isoformat(),
                "rain_tomorrow": saved["result"].rain,
                "rain_probability": saved["result"].probability,
                "model": MODEL_PATH.name,
                "observations": features.iloc[0].to_dict(),
            }
            st.download_button("Download forecast (JSON)", json.dumps(report, indent=2),
                               file_name=f"rainfall-{observed_on.isoformat()}.json", mime="application/json", width="stretch")
            try:
                drivers = top_drivers(pipeline, features)
            except Exception:
                logger.exception("Could not explain forecast")
                drivers = []
            if drivers:
                scale = max(abs(d.push) for d in drivers) or 1.0
                rows = "".join(
                    f'<li><div class="driver-head"><strong>{escape(d.label)}</strong><span>{escape(d.value)}</span></div>'
                    f'<div class="driver-bar {"up" if d.push > 0 else "down"}"><i style="width:{abs(d.push) / scale * 50:.1f}%"></i></div>'
                    f'<small>{"Pushes toward rain" if d.push > 0 else "Pushes toward dry"}</small></li>'
                    for d in drivers
                )
                st.html(f"""
                    <section class="drivers"><h3>Key influences</h3>
                    <div class="driver-scale"><span>Less rain</span><span>More rain</span></div>
                    <ul>{rows}</ul>
                    </section>
                """)

    if locations:
        st.html('<div id="stations"></div>')
        with st.expander("Weather stations"):
            render_station_map(locations, map_result)
    st.html("""
        <footer>
            <span><strong>Monsoon</strong><span class="footer-separator"> / </span>Nepal rainfall forecasting</span>
            <span>Data from Open-Meteo. Model: XGBoost.</span>
            <span><a href="https://www.kaggle.com/code/bashcode223/rainfall-prediction-nepal-rf-ann-xgb" target="_blank" rel="noopener">Kaggle notebook</a></span>
        </footer>
    """)


if __name__ == "__main__":
    main()

