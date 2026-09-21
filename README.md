# Monsoon — Nepal rainfall prediction

A Streamlit app for predicting next-day rain from late-day weather observations. It includes a fitted XGBoost pipeline, 11 trained stations, validated weather inputs, a probability display, and a downloadable JSON report.

## Run locally

Use Python 3.12. From this directory:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Data Processing and Models Training with Comparison (ANN, XGB $ Random Forest) is done at "github: https://github.com/dols30/Rainfall-Prediction-Nepal-RF-ANN-XGB"

Choose a city on the interactive map (or in the station dropdown) and an observation date, enter the day's measurements across the four tabs, then choose **Generate forecast**. Search cities and use the map zoom controls to explore the seven provinces. Map selections and the station dropdown stay synchronized. Rain forecasts show a rain cloud; no-rain forecasts show a sun. Input defaults are examples, not current weather. Editing inputs hides the previous forecast until you run it again. Reset restores the example measurements and today's Nepal date, retaining the selected station.

## Model provenance

The saved September 14 artifact was produced with scikit-learn 1.1.3. It is not compatible with the current runtime. The included pipeline is reproduced from the XGBoost section of `Nepal_RainTomorrow_Clean_Final.ipynb`, using the supplied `Nepal_Weather_2010_2026.csv`. The original files are untouched. Library changes can produce different fitted trees and scores; this is a new fitted artifact, not a byte-for-byte conversion of the original.

`Nepal_Rainfall_XGBoost_Model.json` records the dataset hash, library versions, date splits, row counts, locations, and held-out evaluation metrics. Training uses the first 80% of unique dates and excludes the day immediately before the test cutoff so its next-day label cannot overlap the test period. No test rows are used for fitting.

To reproduce the pipeline:

```sh
python train.py /path/to/Nepal_Weather_2010_2026.csv
```

To load a different compatible, trusted local artifact, set `RAINFALL_MODEL_PATH` to its absolute path. Only load pickle/joblib files you trust; they can execute code. There is intentionally no public model-upload endpoint. A replacement must expose the same 25 raw columns, binary labels (0/1), and the notebook's fitted location encoder. Install the package versions used to train it.

## Input contract

- Temperature: °C; rainfall and evaporation: mm; sunshine: hours.
- Humidity and cloud cover: 0–100 percent. Wind speed: km/h. Wind direction: 0–360 degrees.
- Pressure: hPa; use the pressure convention of the supplied dataset (values are approximately 988–1031 hPa).
- `RainToday = int(Rainfall > 1.0)`, checked against every row of the supplied dataset.
- Calendar features come from the observation date, with Monday = 0.
- Stations are read from the fitted encoder, not a hand-maintained city list.

This is a late-day next-day prediction, because it requires 3 PM observations and the day's rainfall total. The app has no live-weather feed. It predicts the binary training label and a model-estimated probability; it does not predict rainfall amount. The dataset's provenance, collection method, and operational validity have not been independently verified. Probabilities have not been independently calibrated. Held-out metrics on this dataset are not evidence of reliable future real-world forecasts.

## Code layout

```text
app.py                    Streamlit layout, input state, and result rendering
assets/style.css          Responsive dashboard styling
assets/station-map.*      Offline interactive map component
rainfall/station_map.py   Map-to-station selection bridge
rainfall/observations.py  Field definitions, validation, and feature construction
rainfall/model.py         Artifact checks and inference
train.py                  Reproducible training and evaluation
tests/                    Validation, real-model, and Streamlit interaction tests
.streamlit/config.toml    Theme and runtime settings
```

## Test

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover rainfall thresholds, calendar features, invalid inputs, all trained stations, column ordering, invalid probabilities, missing-model handling, prediction, edits, and reset. No synthetic prediction mode is used.

## Deployment

The app can run on a Streamlit host with Python 3.12 and these pinned dependencies. Include the model, application files, and `.streamlit` directory. Launch `streamlit run app.py`. No API keys are needed. Review dataset/model redistribution rights before publishing the artifact. This project has been deployed publicly at "https://monsoonai.streamlit.app".

## Map attribution

The map follows Nepal’s post-May-2020 outline, including the northwestern extension. Boundary, province, and city coordinate sources and licenses are documented in `assets/MAP-SOURCES.md`. The map is illustrative; city points are not surveyed station positions.
