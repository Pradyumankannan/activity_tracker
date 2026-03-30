import datetime
import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = LOGS_DIR / "activity_log.db"


def get_connection():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app TEXT NOT NULL,
                title TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                idle_time REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_report_summaries (
                report_date TEXT PRIMARY KEY,
                session_count INTEGER NOT NULL,
                total_tracked_seconds REAL NOT NULL,
                total_idle_seconds REAL NOT NULL,
                total_active_seconds REAL NOT NULL,
                category_summary_json TEXT NOT NULL,
                top_apps_json TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_report_summaries (
                week_start_date TEXT PRIMARY KEY,
                week_end_date TEXT NOT NULL,
                session_count INTEGER NOT NULL,
                total_tracked_seconds REAL NOT NULL,
                total_idle_seconds REAL NOT NULL,
                total_active_seconds REAL NOT NULL,
                category_summary_json TEXT NOT NULL,
                top_apps_json TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_table_info(table_name):
    with get_connection() as conn:
        return conn.execute(f"PRAGMA table_info({table_name})").fetchall()


def descTable():
    return get_table_info("activity_log")


def getRowsInTimeframe(start_time, end_time):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM activity_log
            WHERE start >= ? AND end <= ?
            """,
            (start_time, end_time),
        ).fetchall()


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


def getLatestTrackedDate():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT start FROM activity_log
            WHERE start IS NOT NULL
            ORDER BY start DESC
            LIMIT 1
            """
        ).fetchone()

    if not row or not row[0]:
        return None

    return datetime.datetime.fromisoformat(row[0]).date().isoformat()


def save_daily_report(
    report_date,
    session_count,
    total_tracked_seconds,
    total_idle_seconds,
    total_active_seconds,
    category_summary,
    top_apps,
):
    generated_at = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_report_summaries (
                report_date,
                session_count,
                total_tracked_seconds,
                total_idle_seconds,
                total_active_seconds,
                category_summary_json,
                top_apps_json,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_date) DO UPDATE SET
                session_count = excluded.session_count,
                total_tracked_seconds = excluded.total_tracked_seconds,
                total_idle_seconds = excluded.total_idle_seconds,
                total_active_seconds = excluded.total_active_seconds,
                category_summary_json = excluded.category_summary_json,
                top_apps_json = excluded.top_apps_json,
                generated_at = excluded.generated_at
            """,
            (
                report_date,
                session_count,
                total_tracked_seconds,
                total_idle_seconds,
                total_active_seconds,
                json.dumps(category_summary),
                json.dumps(top_apps),
                generated_at,
            ),
        )
        conn.commit()


def get_daily_report(report_date):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM daily_report_summaries
            WHERE report_date = ?
            """,
            (report_date,),
        ).fetchone()


def save_weekly_report(
    week_start_date,
    week_end_date,
    session_count,
    total_tracked_seconds,
    total_idle_seconds,
    total_active_seconds,
    category_summary,
    top_apps,
):
    generated_at = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO weekly_report_summaries (
                week_start_date,
                week_end_date,
                session_count,
                total_tracked_seconds,
                total_idle_seconds,
                total_active_seconds,
                category_summary_json,
                top_apps_json,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_start_date) DO UPDATE SET
                week_end_date = excluded.week_end_date,
                session_count = excluded.session_count,
                total_tracked_seconds = excluded.total_tracked_seconds,
                total_idle_seconds = excluded.total_idle_seconds,
                total_active_seconds = excluded.total_active_seconds,
                category_summary_json = excluded.category_summary_json,
                top_apps_json = excluded.top_apps_json,
                generated_at = excluded.generated_at
            """,
            (
                week_start_date,
                week_end_date,
                session_count,
                total_tracked_seconds,
                total_idle_seconds,
                total_active_seconds,
                json.dumps(category_summary),
                json.dumps(top_apps),
                generated_at,
            ),
        )
        conn.commit()


def get_weekly_report(week_start_date):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM weekly_report_summaries
            WHERE week_start_date = ?
            """,
            (week_start_date,),
        ).fetchone()
