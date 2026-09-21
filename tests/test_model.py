from datetime import date
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from rainfall.model import load_pipeline, predict, trained_locations
from rainfall.observations import FIELDS, build_features


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pipeline():
    return load_pipeline(ROOT / "Nepal_Rainfall_XGBoost_Model.pkl")


def frame(location="Kathmandu"):
    return build_features(date(2026, 9, 18), location, {field.name: field.default for field in FIELDS})


def test_all_trained_stations_predict(pipeline):
    locations = trained_locations(pipeline)
    assert len(locations) == 11
    for location in locations:
        result = predict(pipeline, frame(location))
        assert isinstance(result.rain, bool)
        assert 0 <= result.probability <= 1


def test_unknown_station_rejected(pipeline):
    with pytest.raises(ValueError, match="not included"):
        predict(pipeline, frame("Unknown"))


def test_reordered_columns_match(pipeline):
    original = frame()
    assert predict(pipeline, original) == predict(pipeline, original[original.columns[::-1]])


@pytest.mark.parametrize("probabilities", [[[np.nan, 0.1]], [[0.4, 0.7]], [[-0.2, 1.2]]])
def test_invalid_model_probabilities_rejected(pipeline, probabilities):
    with patch.object(pipeline, "predict_proba", return_value=probabilities):
        with pytest.raises(ValueError, match="invalid probabilities"):
            predict(pipeline, frame())
