# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import sys
import multiprocessing
import traceback
import logging
logger = logging.getLogger(__name__)

import checks
import files
from SetupWindow import SetupWindow
from tkinter.messagebox import showerror


def main():
    # set up logging
    logger.info("Starting main")
    logger.info("Program Arguments: " + str(sys.argv))
    
    # try loading config.json
    configs = files.load_config()

    # show setup window
    if configs is None or len(sys.argv) < 2:
        logger.info("Starting Setup")
        setupwindow = SetupWindow()
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
        # import json
        # json.dumps(configs, indent=2, default=files.path_default)

        from PPDWindow import PPDWindow
        ppd_window = PPDWindow(file, configs)
        ppd_window.mainloop()
        logger.info("Disambiguation Finished")
    logger.info("Exitting Main")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
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
    checks.join_close_thread()
    logger.info("Shutting down logging and remixing logs to ppd.log")
    logging.shutdown()
    files.remix_logs()
