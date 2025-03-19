# consts.py, Charlie Jordan, 3/7/2025

import sys
import os
from pathlib import Path
import psutil
import re
import logging
logger = logging.getLogger(__name__)

PPD_DIR = Path(__file__).resolve().parent

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # print('> running in a PyInstaller bundle')
    IS_BUNDLED = True
    EXE_DIR = Path(sys.executable).resolve().parent
else:
    # print('> running in a normal Python process')
    IS_BUNDLED = False
    EXE_DIR = PPD_DIR

# determine where to put log
# find a parent process if it exists from the log folders and return it
# also handles making folders if they don't exist or if this is the main process
def get_log_folder():
    this_pid = os.getpid()
    parent_pids = [p.pid for p in psutil.Process(this_pid).parents()]
    if not LOGS_DIR.exists():
        os.mkdir(LOGS_DIR)
    for path in LOGS_DIR.glob('logs*'):
        if path.is_dir():
            m = re.match(r'^logs(\d+)$', path.name)
            if m:
                pid = int(m[1])
                if pid in parent_pids:
                    return path
    log_folder = LOGS_DIR / f"logs{this_pid}"
    if not log_folder.exists():
        os.mkdir(log_folder)
    return log_folder

LOGS_DIR = EXE_DIR / 'logs'
LOG_COPY_LOCK_FILE = EXE_DIR / '.logcopylock'
LOG_FILENAME = "ppd{}.log"
log_path = get_log_folder() / LOG_FILENAME.format(os.getpid())
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(filename=log_path, mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s.%(msecs)03d | P%(process)05d-T%(thread)05d | %(levelname)s | %(funcName)16s : %(message)s',
    datefmt='%H:%M:%S'
)

logger.info("IS_BUNDLED: %s", IS_BUNDLED)
logger.info("EXE_DIR: %s", EXE_DIR)

# sys.executable is the location of the exe
# print("> PPD_DIR:", PPD_DIR)
# print("> EXE_DIR:", EXE_DIR)

DEFAULT_PSLF_DIR_PATH = Path(r"C:\Program Files\GE PSLF")
DEFAULT_PSSE_DIR_PATH = Path(r"C:\Program Files\PTI\PSSE35\35.6")

PSLF_EXE_SUFFIX = "Pslf.exe"
DEFAULT_PSSE_EXE_SUFFIX = "PSSBIN/psse35.exe"
PSSE_EXE_SUFFIX = DEFAULT_PSSE_EXE_SUFFIX
PSLF_PY_SUFFIX = "PslfPython/PSLF_PYTHON.py"
PSSE_PY_SUFFIX = "PSSPY311/psse35.py"


CONFIG_FILENAME = ".ppd-config.json"
HISTORY_FILENAME = ".history.json"

BG_COLOR = "#E6E6FA" #"#FCFFF3"
