# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import sys
import multiprocessing
import traceback
import logging
from tkinter.messagebox import showerror
logger = logging.getLogger(__name__)

import checks
import files
import consts
from updatecheck import start_check_for_update, AvailableUpdateWindow
from SetupWindow import SetupWindow
from PPDWindow import PPDWindow


def main():
    # set up logging
    logger.info("Starting main. PPD Version: %d", consts.VERSION)
    logger.info("Program Arguments: " + str(sys.argv))
    
    logger.info("Starting check for update.")
    update_thread = start_check_for_update()
    
    # try loading config.json
    configs = files.load_config()

    # show setup window
    if configs is None or len(sys.argv) < 2:
        logger.info("Starting Setup")
        setupwindow = SetupWindow(configs)
        setupwindow.mainloop()
        
        if not setupwindow.done:
            logger.info("Setup Cancelled")
            logger.info("done - %s", setupwindow.done)
            return
        configs = files.load_config()
        if not configs:
            logger.warning("Setup Failure")
            logger.warning("configs - %s", configs)
            return
        logger.info("Setup Success")
        
    # do normal disambiguation
    if len(sys.argv) > 1:
        logger.info("Starting Disambiguation")
        file = sys.argv[1]
        logger.info(f"File: '{file}'")

        ppd_window = PPDWindow(file, configs)
        ppd_window.mainloop()
        logger.info("Disambiguation Finished")
    
    logger.info("Joining update check thread")
    update_thread.join()
    if update_thread.result:
        logger.info("Update Available")
        update_window = AvailableUpdateWindow()
        update_window.mainloop()
    else:
        logger.info("No Update Available")
    
    logger.info("Exitting Main")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
        checks.join_close_thread()
    except Exception as e:
        logger.error("==========================")
        logger.error("Main Encountered an error:")
        logger.error("==========================")
        tb = ''.join(traceback.format_exception(e))
        for line in tb.split('\n'):
            logger.error(line)
        logger.error("==========================")
        showerror(
            "PPD Fatal Error",
            message="PSLF PSSE Disambiguator encountered a fatal error. "
                    "Include ppd.log and the save file you tried to open with"
                    " your bug report. Traceback:\n" + tb
        )
    # input("Press Enter to close")
    logger.info("Shutting down logging and remixing logs to ppd.log")
    logging.shutdown()
    files.remix_logs()
