from dataclasses import dataclass
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.exceptions import InconsistentVersionWarning

from rainfall.observations import FEATURES


@dataclass(frozen=True)
class Forecast:
    rain: bool
    probability: float


def load_pipeline(path: Path) -> Pipeline:
    """Load a trusted, locally configured artifact; never accept pickle uploads."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        pipeline = joblib.load(path)
    if not isinstance(pipeline, Pipeline) or not hasattr(pipeline, "predict_proba"):
        raise ValueError("Save the fitted preprocessing + classifier pipeline, not just the classifier.")
    names = list(getattr(pipeline, "feature_names_in_", []))
    if set(names) != set(FEATURES) or len(names) != len(FEATURES):
        raise ValueError("The saved pipeline's input columns do not match the Nepal weather notebook.")
    classes = list(getattr(pipeline, "classes_", []))
    if len(classes) != 2 or set(classes) != {0, 1}:
        raise ValueError("The pipeline must use 0 for no rain and 1 for rain.")
    return pipeline


def trained_locations(pipeline: Pipeline) -> tuple[str, ...]:
    """Read station names from the fitted encoder used in the source notebook."""
    try:
        preprocessor = pipeline.named_steps["preprocessor"]
        encoder = preprocessor.named_transformers_["location"].named_steps["onehot"]
        locations = tuple(sorted(str(value) for value in encoder.categories_[0]))
    except (KeyError, AttributeError, IndexError) as exc:
        raise ValueError("Cannot read the fitted location encoder. Use the pipeline from train.py.") from exc
    if not locations:
        raise ValueError("The pipeline has no trained locations.")
    return locations


def predict(pipeline: Pipeline, features: pd.DataFrame) -> Forecast:
    if features.iloc[0]["Location"] not in trained_locations(pipeline):
        raise ValueError("This location was not included in training.")
    ordered = features.loc[:, list(pipeline.feature_names_in_)]
    probabilities = np.asarray(pipeline.predict_proba(ordered))
    if probabilities.shape != (1, 2) or not np.isfinite(probabilities).all():
        raise ValueError("The model returned invalid probabilities.")
    if (probabilities < 0).any() or (probabilities > 1).any() or not np.isclose(probabilities.sum(), 1):
        raise ValueError("The model returned invalid probabilities.")
    rain_index = list(pipeline.classes_).index(1)
    prediction = pipeline.predict(ordered)[0]
    if prediction not in (0, 1):
        raise ValueError("The model returned an unexpected prediction label.")
    return Forecast(rain=bool(prediction), probability=float(probabilities[0, rain_index]))
