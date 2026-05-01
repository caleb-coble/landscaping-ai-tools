import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from final_processor import process_timesheet, update_spreadsheet

WATCH_FOLDER = "timesheet_uploads"
PROCESSED_FILES = set()

class TimesheetHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        if filepath in PROCESSED_FILES:
            return
            
        if filename.endswith((".heic", ".HEIC")):
            print(f"New timesheet detected: {filename}")
            PROCESSED_FILES.add(filepath)
            time.sleep(1)
            result = process_timesheet(filepath)
            update_spreadsheet(result)

            try:
                os.remove(filepath)
            except:
                pass


if __name__ == "__main__":
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

