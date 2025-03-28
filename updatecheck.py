# updatecheck.py, Charlie Jordan, 3/28/2025

import re
from urllib.request import urlopen
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser
import datetime
import logging
logger = logging.getLogger(__name__)

import consts

SNOOZE_FILE_NAME = "snooze until.txt"

def start_check_for_update():
    """
    Start an update check. Returns a daemon thread. Use .join() to wait for the
    thread to finish, then get the result of the update check from the .result
    member. True means that there is an update available.

    :return: A running thread object.
    """
    t = UpdateCheckThread()
    logger.info("Start check for update")
    t.start()
    logger.info("Returning")
    return t

class UpdateCheckThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, daemon=True)
        self.result = False
    
    def run(self):
        logger.info("Running UpdateCheckThread")
        try:
            with open(consts.EXE_DIR / SNOOZE_FILE_NAME, 'r') as fp:
                date = datetime.datetime.fromisoformat(fp.read())
                # if we're snoozing then result should stay false
                logger.info(f"Found snooze until date: {date}")
                if datetime.datetime.now() < date:
                    logger.info("Snoozing, returning")
                    return
        except OSError:
            logger.info("OSError while checking for snooze until file")
            pass
        try:
            logger.info("Opening url.")
            with urlopen(consts.GITHUB_REPO_URL, timeout=2) as response:
                logger.info(f"HTTP response: {response}")
                resolved_url: str = response.url
                logger.info(f"Resolved URL: {resolved_url}")
        except Exception as e:
            logger.info(f"Error during urlopen: {e}")
            return
        m = re.search(r"releases/tag/v(\d+)$", resolved_url)
        if m:
            logger.info(f"Response url matched regular expression")
            remote_version = int(m[1])
            if remote_version > consts.VERSION:
                logger.info(f"Remote version greater")
                self.result = True
            else:
                logger.info(f"Remote version not greater")
        else:
            logger.info(f"Response url did not match regular expression")

class AvailableUpdateWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        logger.info("Building AvailableUpdateWindow")

        self.title("PPD Update Available")
        self.iconphoto(True, tk.PhotoImage(file=consts.IMG_DIR / "ppd.png"))
        self.config(bg=consts.BG_COLOR)
        self.resizable(False, False)
        self.bind("<Escape>", lambda e: self.destroy())
        style = ttk.Style()
        style.configure(".", background=consts.BG_COLOR)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.focus_force()

        self.update_label = ttk.Label(self, text="An update to PSLF PSSE Disambiguator is available")
        self.update_label.grid(row=0, column=0, columnspan=3)
        
        self.update_button = ttk.Button(self, text="Update",
                command=self.update_callback)
        self.update_button.grid(row=0, column=3)
        
        self.snooze_label_L = ttk.Label(self, text="Snooze for")
        self.snooze_label_L.grid(row=1, column=0, sticky='e')
        
        vcmd = (self.register(self.validate_entry), '%P')
        self.snooze_entry = ttk.Entry(self, width=5, validate="key", validatecommand=vcmd)
        self.snooze_entry.insert(0, '1')
        self.snooze_entry.grid(row=1, column=1)
        
        self.snooze_label_R = ttk.Label(self, text="days.")
        self.snooze_label_R.grid(row=1, column=2, sticky='w')
        
        self.snooze_button = ttk.Button(self, text="Snooze",
                command=self.snooze_callback)
        self.snooze_button.grid(row=1, column=3)

        for widget in self.winfo_children():
            widget.grid_configure(padx=3, pady=4)
        
    def validate_entry(self, new_val):
        if new_val == '':
            return True
        try:
            float(new_val)
        except ValueError:
            return False
        return True

    def update_callback(self):
        logger.info("Running update_callback")
        webbrowser.open_new_tab(consts.GITHUB_REPO_URL)
        self.destroy()

    def snooze_callback(self):
        logger.info("Running snooze_callback")
        snooze_days = float(self.snooze_entry.get() or '0')
        try:
            with open(consts.EXE_DIR / SNOOZE_FILE_NAME, 'w') as fp:
                date = datetime.datetime.now() + datetime.timedelta(days=snooze_days)
                iso_date = date.isoformat()
                logger.info(f"Writing snooze_time: {iso_date}")
                fp.write(iso_date)
        except OSError as e:
            logger.error(f"Encountered OSError while writing {SNOOZE_FILE_NAME}: {e}")
        self.destroy()