import win32gui
import win32process
import psutil 
from time import sleep
import json 
from datetime import datetime
import ctypes
import ctypes.wintypes

from dbHelper import get_connection, initialize_database
from ML.predict import predict_category

FULLSCREEN_THRESHOLD = 20  # seconds
NORMAL_THRESHOLD = 10  # seconds

def insert_log_entry(entry):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO activity_log (app, title, start, end, duration_seconds, idle_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry["app"],
                entry["title"],
                entry["start"],
                entry["end"],
                entry["duration_seconds"],
                entry["idle_time"],
            ),
        )
        conn.commit()

def get_idle_time():
    """Returns idle time in seconds on Windows."""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("dwTime", ctypes.c_uint),
        ]
    
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input)):
        millis = ctypes.windll.kernel32.GetTickCount() - last_input.dwTime
        return millis / 1000.0
    else:
        return 0


def get_active_window_title():
    """Returns the title of the currently active window."""
    window = win32gui.GetForegroundWindow()
    window_title = win32gui.GetWindowText( window )

    _, pid = win32process.GetWindowThreadProcessId( window )

    try:
        process = psutil.Process( pid )
        process_name = process.name()
    except psutil.Error:
        process_name = "Unknown"

    return process_name, window_title

def is_fullscreen():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    return (rect.left <= 0 and rect.top <= 0 and
            rect.right >= screen_width and rect.bottom >= screen_height)

def track_active_windows():
    last_app, last_title = get_active_window_title()
    last_start_time = datetime.now()
    idle_seconds = 0
    print("Tracker started. Ctrl + C to stop.\n")
    prev_idle = 0
    idle_time = 0
    try:
        prev_idle = 0
        while True:
            app, title = get_active_window_title()
            idle_seconds = get_idle_time()

            if app != last_app or title != last_title:
                now = datetime.now()
                if last_app is not None:
                    duration_seconds = (now - last_start_time).total_seconds()
                    entry = {
                        "app": last_app,
                        "title": last_title,
                        "start": last_start_time.isoformat(),
                        "end": now.isoformat(),
                        "duration_seconds": duration_seconds,
                        "idle_time": min(idle_time, duration_seconds),
                    }
                write_log(entry)
                
                # update new session
                last_app, last_title = app, title
                last_start_time = now
                idle_time = 0
                prev_idle = 0

            idle_threshold = FULLSCREEN_THRESHOLD if is_fullscreen() else NORMAL_THRESHOLD
            # print( prev_idle, idle_seconds, idle_threshold, idle_time )
            if prev_idle > idle_seconds:
                if prev_idle >= idle_threshold:
                    idle_time += prev_idle
            
            prev_idle = idle_seconds
            sleep(1)

    except KeyboardInterrupt:
        print("\nTracker stopped.")

def write_log(entry):
    insert_log_entry(entry)
    print("LOGGED:", entry)
    print(
        predict_category(
            entry["app"],
            entry["title"],
            duration_seconds=entry.get("duration_seconds", 0),
            idle_time_seconds=entry.get("idle_time", 0),
            start=entry.get("start"),
        )
    )
    

initialize_database()
track_active_windows()
