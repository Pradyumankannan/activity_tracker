import sqlite3
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

from ML.predict import predict_category

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = LOGS_DIR / "activity_log.db"

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

# plotting
def plotting(df):
    if df.empty:
        print("No data to plot")
        return

    plot_df = df.copy()
    plot_df["duration_seconds"] = pd.to_numeric(
        plot_df["duration_seconds"], errors="coerce"
    ).fillna(0)

    summary = (
        plot_df.groupby("predicted_category")["duration_seconds"]
        .sum()
        .sort_values(ascending=False)
    )

    if summary.empty:
        print("No category data to plot")
        return

    minutes = summary / 60

    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(minutes.index, minutes.values, color="steelblue", edgecolor="black")

    ax.set_title("Time Spent by Predicted Category", fontsize=16, fontweight="bold")
    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Time (minutes)", fontsize=12)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.1f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    plt.show()

rows = getRowsForDay("2026-03-24")
df = rowsToPandas(rows)
df = addPredictedLabels(df)
plotting(df)

