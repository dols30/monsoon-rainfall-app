from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_prediction_edit_and_reset():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert len(app.selectbox[0].options) == 11
    app.button[0].click().run()
    assert not app.exception
    assert "forecast" in app.session_state
    app.number_input(key="MaxTemp").set_value(30.0).run()
    assert any("Observations changed" in message.value for message in app.info)
    app.button[1].click().run()
    assert "forecast" not in app.session_state
    assert app.number_input(key="MaxTemp").value == 28.0
    assert not app.exception


def test_invalid_temperature_disables_prediction():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.number_input(key="MinTemp").set_value(40.0).run()
    assert app.button[0].disabled
    assert any("minimum temperature" in message.value for message in app.error)


def test_missing_model_shows_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("RAINFALL_MODEL_PATH", str(tmp_path / "missing.pkl"))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert app.button[0].disabled
    assert any("saved model is missing" in message.value for message in app.warning)
