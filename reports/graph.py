import sqlite3
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = LOGS_DIR / "activity_log.db"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.predict import predict_category
from reports.plotHelper import plotIdleVsActive, plotting, plotTopApps

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  window_title TEXT)''')
    conn.commit()
    conn.close()

# get columns from database
def descTable():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(activity_log)")
    columns = c.fetchall()
    conn.close()
    return columns

# get values from timeframe
def getRowsInTimeframe(start_time, end_time):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM activity_log
        WHERE start >= ? AND end <= ?
        """,
        (start_time, end_time),
    )
    rows = c.fetchall()
    conn.close()
    return rows

# get values for a specific day
def getRowsForDay(date):
    start_time = f"{date}T00:00:00"
    end_time = f"{date}T23:59:59"
    return getRowsInTimeframe(start_time, end_time)

def getRowsForWeek(week_start_date):
    start_date = datetime.datetime.fromisoformat(week_start_date)
    end_date = start_date + datetime.timedelta(days=7)
    start_time = start_date.isoformat()
    end_time = end_date.isoformat()
    return getRowsInTimeframe(start_time, end_time)

def getRowsForMonth(month_start_date):
    start_date = datetime.datetime.fromisoformat(month_start_date)
    if start_date.month == 12:
        end_date = datetime.datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime.datetime(start_date.year, start_date.month + 1, 1)
    start_time = start_date.isoformat()
    end_time = end_date.isoformat()
    return getRowsInTimeframe(start_time, end_time)

# rows from database to pandas
def rowsToPandas(rows):
    columns = [column[1] for column in descTable()]
    return pd.DataFrame(rows, columns=columns)

# predict and add label column
def addPredictedLabels(df):
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

# Get average duration of sessions for each category
def avgSession(df):
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce").fillna(0)
    avg_duration = df.groupby("predicted_category")["duration_seconds"].mean() / 60
    avg_duration = avg_duration.sort_values(ascending=False)
    return avg_duration

rows = getRowsForDay("2026-03-24")
df = rowsToPandas(rows)
df = addPredictedLabels(df)

plotting(df)
plotTopApps(df)
print(avgSession(df))