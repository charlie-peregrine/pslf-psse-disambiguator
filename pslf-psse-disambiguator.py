# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import subprocess
import sys
from pathlib import Path
import multiprocessing
import traceback
import logging
logger = logging.getLogger(__name__)

import consts
import checks
import files
from SetupWindow import SetupWindow
from tkinter.messagebox import showerror


def run_program(program, file):
    # add a process layer to avoid directory change effects
    p = multiprocessing.Process(target=_run_program, args=(program, file))
    p.start()
    p.join()

def _run_program(program, file):
    command_format = 'cd "{work_dir}" & "{exe}" "{file}"'
    work_dir = str(Path(file).parent)
    logger.info("run_program start")
    
    def popen(cmd):
        return subprocess.Popen(cmd,shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    if program == 'pslf':
        suffix = consts.PSLF_EXE_SUFFIX
    elif program == 'psse':
        suffix = consts.PSSE_EXE_SUFFIX
    else:
        command_text = command_format.format(
            work_dir=work_dir, exe=program, file=file
        )
        logger.info("Generic command text:", command_format)

        logger.info("Starting subprocess.")
        p = popen(command_text)
        logger.info("Subprocess started.")
        return p
    
    config = files.load_config()
    if config is None:
        raise KeyError("Configuration file not found")
    
    exe = Path(config[program]) / suffix
    command_text = command_format.format(work_dir=work_dir, exe=exe, file=file)
    logger.info(program + " command_text: " + command_text)
    
    logger.info("Starting subprocess.")
    p = popen(command_text)
    logger.info("Subprocess started.")
    import os
    logger.info("os.getcwd(): %s", os.getcwd())
    return p

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
        # maybe add something here where if the user is holding down control
        # we disable skip prompt.

        # try:
        #     raise KeyboardInterrupt
        # except KeyboardInterrupt:
        #     raise KeyError

        # from PPDWindow import PPDWindow
        # ppd_window = PPDWindow()
        # ppd_window.mainloop()
        # print("wowee")
        # return

        # open history and check if the file is there
        hist_prog = checks.history_check(file)
        logging.info(f"history_check result: '{hist_prog}'")
        if configs['skip_prompt'] and hist_prog:
            logging.info(f"Starting {file} in {hist_prog}")
            run_program(hist_prog, file)
            return
        
        # check the header bytes
        bytes_prog = checks.bytes_check(file)
        logging.info(f"bytes_check result: '{bytes_prog}'")
        if configs['skip_prompt'] and bytes_prog:
            logging.info(f"Starting {file} in {bytes_prog}")
            p = run_program(bytes_prog, file)
            files.history_set(file, bytes_prog)
            return

        # if this is the right version to use the python libraries then check
        # if the program can be run with those.
        open_prog = ''
        if configs['use_python']:
            logging.info("running open_check.")
            open_prog = checks.open_check(file)
            logging.info(f"open_check result: '{open_prog}'")
            if configs['skip_prompt'] and open_prog:
                logging.info(f"Starting {file} in {open_prog}")
                run_program(open_prog, file)
                files.history_set(file, open_prog)
                return
        else:
            logging.info("skipping open_check.")

        
        
        
        # open a window here showing the prompt
        # if user wants a different program open file dialog for C:\ProgramData\Microsoft\Windows\Start Menu\Programs
        
        print("prompt time")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except Exception as e:
        logger.error("==========================")
        logger.error("Main Encountered an error:")
        logger.error("==========================")
        tb = ''.join(traceback.format_exception(e))
        map(logger.error, tb.split('\n'))
        logger.error("==========================")
        showerror(
            "PPD Fatal Error",
            message="PSLF PSSE Disambiguator encountered a fatal error. "
                    "Include ppd.log and the save file you tried to open with"
                    " your bug report. Traceback:\n" + tb
        )
    # input("Press Enter to close")
    checks.join_close_thread()
    logging.shutdown()
    files.remix_logs()
