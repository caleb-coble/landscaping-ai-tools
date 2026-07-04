import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from final_processor import process_timesheet, update_spreadsheet

WATCH_FOLDER = "timesheet_uploads"
PROCESSED_FILES = set()
IMAGE_EXTENSIONS = (".heic", ".HEIC", ".jpg", ".jpeg", ".JPG", ".JPEG")


def wait_for_file_ready(filepath, timeout=30, stable_seconds=1):
    """Wait until a file exists and its size stops changing."""
    deadline = time.time() + timeout
    last_size = -1
    stable_since = None

    while time.time() < deadline:
        if not os.path.exists(filepath):
            time.sleep(0.2)
            continue

        try:
            size = os.path.getsize(filepath)
        except OSError:
            time.sleep(0.2)
            continue

        if size == last_size and size > 0:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= stable_seconds:
                return True
        else:
            last_size = size
            stable_since = None

        time.sleep(0.2)

    return False


class TimesheetHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)

        if filepath in PROCESSED_FILES:
            return

        if not filename.endswith(IMAGE_EXTENSIONS):
            return

        print(f"New timesheet detected: {filename}")
        PROCESSED_FILES.add(filepath)

        if not wait_for_file_ready(filepath):
            print(f"Timed out waiting for file to finish copying: {filename}")
            PROCESSED_FILES.discard(filepath)
            return

        try:
            result = process_timesheet(filepath)
            rows_added = update_spreadsheet(result)
            print(f"Added {rows_added} row(s) from {filename}")
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            PROCESSED_FILES.discard(filepath)
            return

        jpg_path = os.path.splitext(filepath)[0] + ".jpg"
        for path in (filepath, jpg_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                print(f"Could not remove {path}: {e}")


if __name__ == "__main__":
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    print("Watching for new timesheets in:", WATCH_FOLDER)

    event_handler = TimesheetHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
