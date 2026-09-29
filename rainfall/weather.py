"""Fetch one day's observations from Open-Meteo and map them onto the model's inputs."""

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from rainfall.observations import FIELDS

MAP_FILE = Path(__file__).resolve().parents[1] / "assets" / "nepal-map.json"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY = ("temperature_2m_max,temperature_2m_min,precipitation_sum,sunshine_duration,"
         "et0_fao_evapotranspiration,wind_gusts_10m_max,wind_direction_10m_dominant")
HOURLY = "temperature_2m,relative_humidity_2m,pressure_msl,cloud_cover,wind_speed_10m,wind_direction_10m"


class WeatherUnavailable(Exception):
    """Raised with a message that is safe to show to the person using the app."""


@lru_cache(maxsize=1)
def _stations() -> dict:
    return {s["name"]: s["coordinates"] for s in json.loads(MAP_FILE.read_text())["stations"]}


def coordinates(location: str) -> tuple[float, float]:
    try:
        longitude, latitude = _stations()[location]
    except KeyError:
        raise WeatherUnavailable(f"No coordinates are stored for {location}.") from None
    return latitude, longitude


def fetch_day(location: str, day: date, today: date | None = None, timeout: float = 10) -> dict:
    """Return {field name: value} for every model input, or raise WeatherUnavailable."""
    latitude, longitude = coordinates(location)
    # The model was trained on the Open-Meteo archive (ERA5), which lags by about five days,
    # so only the last week comes from the forecast endpoint.
    recent = ((today or date.today()) - day) <= timedelta(days=7)
    query = urlencode({
        "latitude": latitude, "longitude": longitude, "start_date": day.isoformat(), "end_date": day.isoformat(),
        "daily": DAILY, "hourly": HOURLY, "timezone": "Asia/Kathmandu", "wind_speed_unit": "kmh",
    })
    try:
        with urlopen(f"{FORECAST_URL if recent else ARCHIVE_URL}?{query}", timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, ValueError) as error:
        raise WeatherUnavailable("Open-Meteo could not be reached. Enter the values by hand, or try again in a moment.") from error
    return parse_day(payload)


def parse_day(payload: dict) -> dict:
    try:
        daily, hourly = payload["daily"], payload["hourly"]
        slot = {stamp[11:16]: index for index, stamp in enumerate(hourly["time"])}

        def at(name: str, clock: str):
            return hourly[name][slot[clock]]

        sunshine = daily["sunshine_duration"][0]
        raw = {
            "MinTemp": daily["temperature_2m_min"][0], "MaxTemp": daily["temperature_2m_max"][0],
            "Temp9am": at("temperature_2m", "09:00"), "Temp3pm": at("temperature_2m", "15:00"),
            "Rainfall": daily["precipitation_sum"][0],
            "Sunshine": None if sunshine is None else sunshine / 3600,
            "Evaporation": daily["et0_fao_evapotranspiration"][0],
            "Humidity9am": at("relative_humidity_2m", "09:00"), "Humidity3pm": at("relative_humidity_2m", "15:00"),
            "WindGustSpeed": daily["wind_gusts_10m_max"][0], "WindGustDir": daily["wind_direction_10m_dominant"][0],
            "WindSpeed9am": at("wind_speed_10m", "09:00"), "WindDir9am": at("wind_direction_10m", "09:00"),
            "WindSpeed3pm": at("wind_speed_10m", "15:00"), "WindDir3pm": at("wind_direction_10m", "15:00"),
            "Pressure9am": at("pressure_msl", "09:00"), "Pressure3pm": at("pressure_msl", "15:00"),
            "Cloud9am": at("cloud_cover", "09:00"), "Cloud3pm": at("cloud_cover", "15:00"),
        }
    except (KeyError, IndexError, TypeError) as error:
        raise WeatherUnavailable("Open-Meteo returned an unexpected response.") from error
    if any(value is None for value in raw.values()):
        raise WeatherUnavailable("Open-Meteo has no complete data for that day yet. Try an earlier date.")
    return {f.name: round(min(max(float(raw[f.name]), f.minimum), f.maximum), 0 if f.step == 1 else 1) for f in FIELDS}
