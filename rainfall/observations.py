from dataclasses import dataclass
from datetime import date
import math

import pandas as pd


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    default: float
    minimum: float
    maximum: float
    step: float = 0.1


TEMPERATURE = (
    Field("MinTemp", "Daily minimum · °C", 18.0, -60.0, 60.0),
    Field("MaxTemp", "Daily maximum · °C", 28.0, -60.0, 60.0),
    Field("Temp9am", "9 AM temperature · °C", 21.0, -60.0, 60.0),
    Field("Temp3pm", "3 PM temperature · °C", 27.0, -60.0, 60.0),
)
MOISTURE = (
    Field("Rainfall", "Today's rainfall · mm", 0.0, 0.0, 1000.0),
    Field("Sunshine", "Sunshine · hours", 7.0, 0.0, 24.0),
    Field("Evaporation", "Evaporation · mm", 4.0, 0.0, 100.0),
    Field("Humidity9am", "9 AM humidity · %", 70.0, 0.0, 100.0, 1.0),
    Field("Humidity3pm", "3 PM humidity · %", 60.0, 0.0, 100.0, 1.0),
)
WIND = (
    Field("WindGustSpeed", "Maximum gust · km/h", 20.0, 0.0, 400.0),
    Field("WindGustDir", "Gust direction · °", 180.0, 0.0, 360.0, 1.0),
    Field("WindSpeed9am", "9 AM speed · km/h", 10.0, 0.0, 400.0),
    Field("WindDir9am", "9 AM direction · °", 180.0, 0.0, 360.0, 1.0),
    Field("WindSpeed3pm", "3 PM speed · km/h", 12.0, 0.0, 400.0),
    Field("WindDir3pm", "3 PM direction · °", 180.0, 0.0, 360.0, 1.0),
)
ATMOSPHERE = (
    Field("Pressure9am", "9 AM pressure · hPa", 1012.0, 800.0, 1100.0),
    Field("Pressure3pm", "3 PM pressure · hPa", 1008.0, 800.0, 1100.0),
    Field("Cloud9am", "9 AM cloud cover · %", 50.0, 0.0, 100.0, 1.0),
    Field("Cloud3pm", "3 PM cloud cover · %", 50.0, 0.0, 100.0, 1.0),
)
FIELDS = TEMPERATURE + MOISTURE + WIND + ATMOSPHERE

# The raw feature order in the training notebook, before preprocessing.
FEATURES = (
    "MaxTemp", "MinTemp", "Rainfall", "Sunshine", "Evaporation",
    "WindGustSpeed", "WindGustDir", "Temp9am", "Humidity9am", "Pressure9am",
    "Cloud9am", "WindSpeed9am", "WindDir9am", "Temp3pm", "Humidity3pm",
    "Pressure3pm", "Cloud3pm", "WindSpeed3pm", "WindDir3pm", "Location",
    "RainToday", "Year", "Month", "Day", "DayOfWeek",
)


def build_features(observed_on: date, location: str, values: dict) -> pd.DataFrame:
    """Validate a single day's observations and derive the notebook features."""
    if not location or not location.strip():
        raise ValueError("Choose a weather station.")
    for field in FIELDS:
        value = values.get(field.name)
        if value is None or not math.isfinite(value):
            raise ValueError(f"Enter a valid value for {field.label}.")
        if not field.minimum <= value <= field.maximum:
            raise ValueError(f"{field.label} must be between {field.minimum:g} and {field.maximum:g}.")
    if values["MinTemp"] > values["MaxTemp"]:
        raise ValueError("Daily minimum temperature cannot exceed the daily maximum.")
    for name in ("Temp9am", "Temp3pm"):
        if not values["MinTemp"] <= values[name] <= values["MaxTemp"]:
            raise ValueError("9 AM and 3 PM temperatures must fall within the daily minimum and maximum.")
    row = {field.name: values[field.name] for field in FIELDS}
    row.update(
        Location=location,
        RainToday=int(values["Rainfall"] > 1.0),
        Year=observed_on.year,
        Month=observed_on.month,
        Day=observed_on.day,
        DayOfWeek=observed_on.weekday(),
    )
    return pd.DataFrame([row], columns=FEATURES)
