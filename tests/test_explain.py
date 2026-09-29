from datetime import date
from pathlib import Path

import numpy as np

from rainfall.explain import contributions, top_drivers
from rainfall.model import load_pipeline
from rainfall.observations import FIELDS, build_features

MODEL = Path(__file__).resolve().parents[1] / "Nepal_Rainfall_XGBoost_Model.pkl"


def test_contributions_add_up_to_the_forecast_probability():
    pipeline = load_pipeline(MODEL)
    features = build_features(date(2025, 7, 15), "Kathmandu", {f.name: f.default for f in FIELDS})
    grouped, base = contributions(pipeline, features)
    probability = 1 / (1 + np.exp(-(base + sum(grouped.values()))))
    assert np.isclose(probability, pipeline.predict_proba(features)[0][1], atol=1e-4)
    drivers = top_drivers(pipeline, features)
    assert len(drivers) == 3 and all(d.label and d.value for d in drivers)
