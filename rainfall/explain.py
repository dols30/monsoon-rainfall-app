"""Explain a forecast with XGBoost's built-in per-feature contributions (no extra packages)."""

import calendar
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from rainfall.observations import FIELDS

UNITS = {f.name: (f.label.split(" · ")[0], f.label.split(" · ")[1] if " · " in f.label else "") for f in FIELDS}
UNITS.update(WindDir9am=("9 AM wind direction", "°"), WindDir3pm=("3 PM wind direction", "°"),
             WindSpeed9am=("9 AM wind speed", "km/h"), WindSpeed3pm=("3 PM wind speed", "km/h"))
UNITS.update(Location=("Weather station", ""), RainToday=("Rain today", ""), Year=("Year", ""),
             Month=("Month", ""), Day=("Day of month", ""), DayOfWeek=("Day of week", ""))


@dataclass(frozen=True)
class Driver:
    label: str
    value: str
    push: float  # model-score contribution; above 0 raises the chance of rain


def contributions(pipeline, features: pd.DataFrame) -> tuple[dict[str, float], float]:
    """Per-input contributions (summed over one-hot columns) and the model's base score."""
    pre, model = pipeline.named_steps["preprocessor"], pipeline.steps[-1][1]
    X = pre.transform(features.loc[:, list(pipeline.feature_names_in_)])
    raw = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True, validate_features=False)[0]
    grouped: dict[str, float] = {}
    for name, value in zip(pre.get_feature_names_out(), raw[:-1]):
        key = name.split("__", 1)[-1]
        key = "Location" if key.startswith("Location_") else key
        grouped[key] = grouped.get(key, 0.0) + float(value)
    return grouped, float(raw[-1])


def _show(name: str, value) -> str:
    if name == "RainToday":
        return "Yes" if int(value) else "No"
    if name == "Month":
        return calendar.month_name[int(value)]
    if name == "DayOfWeek":
        return calendar.day_name[int(value)]
    if name in ("Location", "Year", "Day"):
        return str(value)
    unit = UNITS[name][1]
    return f"{float(value):g} {unit}".strip()


def top_drivers(pipeline, features: pd.DataFrame, count: int = 3) -> list[Driver]:
    grouped, _ = contributions(pipeline, features)
    ranked = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:count]
    row = features.iloc[0]
    return [Driver(UNITS[name][0], _show(name, row[name]), push) for name, push in ranked]
