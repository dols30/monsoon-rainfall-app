from datetime import date
from pathlib import Path
from urllib.error import URLError

import pytest
from streamlit.testing.v1 import AppTest

from rainfall import weather
from rainfall.observations import FIELDS

APP = Path(__file__).resolve().parents[1] / "app.py"


def payload(**daily):
    hours = [f"2026-09-29T{h:02d}:00" for h in range(24)]
    series = lambda fn: [fn(h) for h in range(24)]
    base = {"temperature_2m_max": [30.04], "temperature_2m_min": [19.96], "precipitation_sum": [2.5],
            "sunshine_duration": [25200.0], "et0_fao_evapotranspiration": [4.2], "wind_gusts_10m_max": [31.0],
            "wind_direction_10m_dominant": [270]}
    return {"daily": {**base, **daily}, "hourly": {
        "time": hours, "temperature_2m": series(lambda h: 20 + h / 2), "relative_humidity_2m": series(lambda h: 90 - h),
        "pressure_msl": series(lambda h: 1000 + h), "cloud_cover": series(lambda h: h * 4),
        "wind_speed_10m": series(lambda h: h), "wind_direction_10m": series(lambda h: h * 10)}}


def test_parse_day_maps_every_model_input():
    values = weather.parse_day(payload())
    assert set(values) == {f.name for f in FIELDS}
    assert values["Sunshine"] == 7.0 and values["MaxTemp"] == 30.0 and values["MinTemp"] == 20.0
    assert values["Temp9am"] == 24.5 and values["Temp3pm"] == 27.5
    assert values["Pressure3pm"] == 1015.0 and values["Cloud9am"] == 36.0 and values["WindDir3pm"] == 150.0


def test_missing_data_is_reported_not_guessed():
    with pytest.raises(weather.WeatherUnavailable):
        weather.parse_day(payload(sunshine_duration=[None]))
    with pytest.raises(weather.WeatherUnavailable):
        weather.parse_day({"daily": {}})


def test_network_failure_becomes_a_friendly_error(monkeypatch):
    def boom(*args, **kwargs):
        raise URLError("offline")
    monkeypatch.setattr(weather, "urlopen", boom)
    with pytest.raises(weather.WeatherUnavailable, match="could not be reached"):
        weather.fetch_day("Kathmandu", date(2026, 9, 29))


def test_old_dates_use_the_archive_endpoint(monkeypatch):
    seen = []

    def spy(url, timeout):
        seen.append(url)
        raise URLError("stop")
    monkeypatch.setattr(weather, "urlopen", spy)
    for day in (date(2026, 9, 25), date(2026, 9, 1)):
        with pytest.raises(weather.WeatherUnavailable):
            weather.fetch_day("Kathmandu", day, today=date(2026, 9, 29))
    assert seen[0].startswith(weather.FORECAST_URL) and seen[1].startswith(weather.ARCHIVE_URL)


def test_button_fills_the_form(monkeypatch):
    filled = {f.name: f.minimum + 1 for f in FIELDS} | {"MinTemp": 15.0, "MaxTemp": 30.0, "Temp9am": 20.0, "Temp3pm": 25.0}
    monkeypatch.setattr(weather, "fetch_day", lambda location, day: filled)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.button(key="autofill").click().run()
    assert not at.exception and at.session_state["MaxTemp"] == 30.0
    assert "Filled from Open-Meteo" in at.success[0].value
