import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "app_category_model.pkl"

FEATURE_COLUMNS = [
    "title",
    "app",
    "duration_seconds",
    "idle_time_seconds",
    "hour",
    "day_of_week",
]

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def predict_category(app, title, duration_seconds=0, idle_time_seconds=0, start=None):
    if start is None:
        start_dt = datetime.now()
    elif isinstance(start, datetime):
        start_dt = start
    else:
        start_dt = pd.to_datetime(start, errors="coerce")
        if pd.isna(start_dt):
            start_dt = datetime.now()

    input_row = pd.DataFrame(
        [
            {
                "title": title or "",
                "app": app or "",
                "duration_seconds": duration_seconds,
                "idle_time_seconds": idle_time_seconds,
                "hour": start_dt.hour,
                "day_of_week": start_dt.weekday(),
            }
        ],
        columns=FEATURE_COLUMNS,
    )

    predicted_category = model.predict(input_row)[0]
    return predicted_category
