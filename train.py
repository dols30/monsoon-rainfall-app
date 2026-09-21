"""Reproduce the XGBoost portion of Nepal_RainTomorrow_Clean_Final.ipynb."""

import argparse
import hashlib
import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import xgboost
from xgboost import XGBClassifier

from rainfall.observations import FEATURES


def train(dataset: Path, output: Path) -> dict:
    data = pd.read_csv(dataset)
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.drop_duplicates().sort_values(["Date", "Location"]).reset_index(drop=True)
    for column in ("RainToday", "RainTomorrow"):
        data[column] = data[column].map({"No": 0, "Yes": 1, 0: 0, 1: 1})
        if data[column].isna().any():
            raise ValueError(f"Unexpected or missing label in {column}.")
        data[column] = data[column].astype(int)
    if not ((data.Rainfall > 1).astype(int) == data.RainToday).all():
        raise ValueError("RainToday does not match the app's rainfall > 1 mm convention.")

    data["Year"] = data.Date.dt.year
    data["Month"] = data.Date.dt.month
    data["Day"] = data.Date.dt.day
    data["DayOfWeek"] = data.Date.dt.dayofweek
    dates = np.sort(data.Date.unique())
    cutoff = pd.Timestamp(dates[int(len(dates) * 0.8)])
    train_mask = data.Date + pd.Timedelta(days=1) < cutoff
    test_mask = data.Date >= cutoff
    features = data.loc[:, list(FEATURES)]
    target = data.RainTomorrow

    preprocessor = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), [name for name in FEATURES if name != "Location"]),
        ("location", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), ["Location"]),
    ])
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
            eval_metric="logloss", n_jobs=-1,
        )),
    ])
    pipeline.fit(features.loc[train_mask], target.loc[train_mask])
    predictions = pipeline.predict(features.loc[test_mask])
    probabilities = pipeline.predict_proba(features.loc[test_mask])[:, 1]
    actual = target.loc[test_mask]
    metadata = {
        "source_notebook": "Nepal_RainTomorrow_Clean_Final.ipynb",
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "training_start": str(data.loc[train_mask, "Date"].min().date()),
        "training_end": str(data.loc[train_mask, "Date"].max().date()),
        "test_start": str(cutoff.date()),
        "test_end": str(data.loc[test_mask, "Date"].max().date()),
        "training_rows": int(train_mask.sum()),
        "test_rows": int(test_mask.sum()),
        "locations": sorted(data.loc[train_mask, "Location"].unique().tolist()),
        "metrics": {
            "accuracy": accuracy_score(actual, predictions),
            "precision": precision_score(actual, predictions),
            "recall": recall_score(actual, predictions),
            "f1": f1_score(actual, predictions),
            "roc_auc": roc_auc_score(actual, probabilities),
        },
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "xgboost": xgboost.__version__, "pandas": pd.__version__, "numpy": np.__version__,
                     "joblib": joblib.__version__},
        "units": {"cloud": "percent", "wind_direction": "degrees", "rain_today": "rainfall > 1 mm"},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output)
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "Nepal_Rainfall_XGBoost_Model.pkl")
    args = parser.parse_args()
    print(json.dumps(train(args.dataset, args.output), indent=2))
