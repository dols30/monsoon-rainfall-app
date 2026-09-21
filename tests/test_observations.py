from datetime import date

import pytest

from rainfall.observations import FIELDS, FEATURES, build_features


def values(**changes):
    return {**{field.name: field.default for field in FIELDS}, **changes}


@pytest.mark.parametrize("rainfall, expected", [(0, 0), (1, 0), (1.1, 1)])
def test_rain_threshold_and_calendar(rainfall, expected):
    frame = build_features(date(2024, 2, 29), "Kathmandu", values(Rainfall=rainfall))
    assert tuple(frame.columns) == FEATURES
    assert frame.loc[0, "RainToday"] == expected
    assert frame.loc[0, "DayOfWeek"] == 3
    assert frame.loc[0, "Month"] == 2
    assert frame.loc[0, "Day"] == 29


@pytest.mark.parametrize("changes", [
    {"MinTemp": 30}, {"Temp3pm": 29}, {"Humidity3pm": 101},
    {"Rainfall": -1}, {"Sunshine": 25}, {"Cloud9am": float("nan")},
    {"WindGustSpeed": float("inf")}, {"Pressure9am": None},
])
def test_invalid_observations(changes):
    with pytest.raises(ValueError):
        build_features(date(2026, 9, 18), "Kathmandu", values(**changes))
