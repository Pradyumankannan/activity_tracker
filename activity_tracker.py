import win32gui
import win32process
import psutil 
from time import sleep
import json 
from datetime import datetime
import os

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

def track_active_windows():
    last_app, last_title = None, None
    last_start_time = datetime.now()

    print("Tracker started. Ctrl + C to stop.\n")

    try:
        while True:
            app, title = get_active_window_title()

            if app != last_app or title != last_title:
                now = datetime.now()

                if last_app is not None:
                    entry = {
                        "app": last_app,
                        "title": last_title,
                        "start": last_start_time.isoformat(),
                        "end": now.isoformat(),
                        "duration_seconds": (now - last_start_time).seconds
                    }
                    write_log(entry)
                    print("LOGGED:", entry)

                # update new session
                last_app, last_title = app, title
                last_start_time = now

            sleep(1)

    except KeyboardInterrupt:
        print("\nTracker stopped.")

def write_log(entry):
    current_directory = os.getcwd()
    logs_path = current_directory + "/logs"
    log_file_path = os.path.join( logs_path, "activity_log.json" )
    with open( log_file_path, "a") as log_file:
        json.dump(entry, log_file)
        log_file.write("\n")

track_active_windows()