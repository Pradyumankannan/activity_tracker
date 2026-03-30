import argparse
import datetime
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dbHelper import getRowsForDay, initialize_database, save_daily_report
from reports.dataHelper import addPredictedLabels, rowsToPandas


def default_report_date():
    return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


def build_daily_report(report_date):
    rows = getRowsForDay(report_date)
    if not rows:
        return None

    df = rowsToPandas(rows)
    df = addPredictedLabels(df)

    df["duration_seconds"] = pd.to_numeric(
        df["duration_seconds"], errors="coerce"
    ).fillna(0)
    df["idle_time"] = pd.to_numeric(df["idle_time"], errors="coerce").fillna(0)
    df["active_time"] = (df["duration_seconds"] - df["idle_time"]).clip(lower=0)

    category_summary = (
        df.groupby("predicted_category")["duration_seconds"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )
    top_apps = (
        df.groupby("app")["duration_seconds"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    return {
        "report_date": report_date,
        "session_count": int(len(df)),
        "total_tracked_seconds": float(df["duration_seconds"].sum()),
        "total_idle_seconds": float(df["idle_time"].sum()),
        "total_active_seconds": float(df["active_time"].sum()),
        "category_summary": category_summary,
        "top_apps": top_apps,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Save a daily activity report into the SQLite database."
    )
    parser.add_argument(
        "--date",
        default=default_report_date(),
        help="Date to summarize in YYYY-MM-DD format. Defaults to yesterday.",
    )
    args = parser.parse_args()

    initialize_database()
    report = build_daily_report(args.date)

    if report is None:
        print(f"No activity rows found for {args.date}. Nothing was written.")
        return

    save_daily_report(
        report_date=report["report_date"],
        session_count=report["session_count"],
        total_tracked_seconds=report["total_tracked_seconds"],
        total_idle_seconds=report["total_idle_seconds"],
        total_active_seconds=report["total_active_seconds"],
        category_summary=report["category_summary"],
        top_apps=report["top_apps"],
    )
    print(f"Saved daily report for {args.date} to the database.")


if __name__ == "__main__":
    main()
