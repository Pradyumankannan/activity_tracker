import pandas as pd
from pathlib import Path
import sys
import pdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dbHelper import descTable
from ML.predict import predict_category

def rowsToPandas(rows):
    columns = [column[1] for column in descTable()]
    return pd.DataFrame(rows, columns=columns)


def addPredictedLabels(df):
    if df.empty:
        labeled_df = df.copy()
        labeled_df["predicted_category"] = pd.Series(dtype="object")
        return labeled_df

    df["predicted_category"] = df.apply(
        lambda row: predict_category(
            row["app"],
            row["title"],
            duration_seconds=row["duration_seconds"],
            idle_time_seconds=row["idle_time"],
            start=row["start"],
        ),
        axis=1,
    )
    return df
