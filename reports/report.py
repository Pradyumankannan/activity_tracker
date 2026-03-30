import pandas as pd
import pdb
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dbHelper import getLatestTrackedDate, getRowsForDay, getRowsForWeek
    from reports.dataHelper import addPredictedLabels, rowsToPandas
    from reports.plotHelper import plotting, plotTopApps
except ModuleNotFoundError:
    from dbHelper import getLatestTrackedDate, getRowsForDay
    from dataHelper import addPredictedLabels, rowsToPandas
    from plotHelper import plotting, plotTopApps

# Get average duration of sessions for each category
def avgSession(df):
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce").fillna(0)
    avg_duration = df.groupby("predicted_category")["duration_seconds"].mean() / 60
    avg_duration = avg_duration.sort_values(ascending=False)
    return avg_duration

#
def idleTime( df ):
    total_idle_time = df["idle_time"].sum() / 60
    print(df["idle_time"].sum())
    return total_idle_time

report_date = "2026-03-20"
rows = getRowsForWeek(report_date)
if not rows:
    latest_tracked_date = getLatestTrackedDate()
    if latest_tracked_date is not None and latest_tracked_date != report_date:
        print(
            f"No rows found for {report_date}. Falling back to latest available date: {latest_tracked_date}."
        )
        report_date = latest_tracked_date
        rows = getRowsForDay(report_date)

df = rowsToPandas(rows)
df = addPredictedLabels(df)

plotting(df)
plotTopApps(df)
print(avgSession(df))
print(idleTime(df))
