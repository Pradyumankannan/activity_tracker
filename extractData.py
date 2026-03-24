import pandas as pd
import json 
import sqlite3
from pathlib import Path

from ML.predict import predict_category

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
LABELED_DATA_DIR = LOGS_DIR / "labeled_data"
DB_PATH = LOGS_DIR / "activity_log.db"


def load_log_dataframe(db_path):
    if not db_path.exists() or db_path.stat().st_size == 0:
        return pd.DataFrame()

    try:
        with sqlite3.connect(db_path) as conn:
            return pd.read_sql_query(
                """
                SELECT app, title, start, end, duration_seconds, idle_time
                FROM activity_log
                ORDER BY id
                """,
                conn,
            )
    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()

x = int( input("Enter the starting index (x): ") )
y = int( input("Enter the ending index (y): ") )
OUTPUT_FILE_PATH = LABELED_DATA_DIR / f"labels{x}_{y}.json"

LABELED_DATA_DIR.mkdir(parents=True, exist_ok=True)

df = load_log_dataframe(DB_PATH)
df = df.iloc[x:y].copy()

df["label"] = df.apply(
    lambda row: predict_category(
        row["app"],
        row["title"],
        duration_seconds=row.get("duration_seconds", 0),
        idle_time_seconds=row.get("idle_time_seconds", row.get("idle_time", 0)),
        start=row.get("start"),
    ),
    axis=1,
)

with open(OUTPUT_FILE_PATH, "w") as f:
    # if the file is not empty, ask before overwriting
    if OUTPUT_FILE_PATH.exists() and OUTPUT_FILE_PATH.stat().st_size > 0:
        overwrite = input(f"{OUTPUT_FILE_PATH} already exists and is not empty. Do you want to overwrite it? (y/n): ")
        if overwrite.lower() != "y":
            print("Aborting. No file was overwritten.")
            exit()
    json.dump(df.to_dict(orient="records"), f, indent=4)
print(f"Labels saved to {OUTPUT_FILE_PATH}")
