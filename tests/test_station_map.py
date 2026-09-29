from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from rainfall.station_map import map_forecast

APP = Path(__file__).resolve().parents[1] / "app.py"


def saved(rain=True, probability=0.62, location="Kathmandu", inputs="x"):
    return {"result": SimpleNamespace(rain=rain, probability=probability), "location": location, "inputs": inputs}


def test_map_gets_the_forecast_for_the_current_station_and_inputs():
    assert map_forecast(saved(), "Kathmandu", "x") == {"location": "Kathmandu", "rain": True, "probability": 0.62}


def test_stale_forecasts_are_not_drawn():
    assert map_forecast(None, "Kathmandu", "x") is None
    assert map_forecast(saved(), "Pokhara", "x") is None
    assert map_forecast(saved(), "Kathmandu", "changed") is None


def test_generating_a_forecast_records_its_station():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="generate").click().run()
    assert not app.exception and app.session_state["forecast"]["location"] == "Kathmandu"
