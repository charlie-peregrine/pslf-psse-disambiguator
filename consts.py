# consts.py, Charlie Jordan, 3/7/2025

import sys
import os
from pathlib import Path
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

LOG_FILENAME = "ppd{}.log"
log_path = EXE_DIR / LOG_FILENAME.format(os.getpid())
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(filename=log_path, mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(relativeCreated)05d | P%(process)5dT%(thread)5d | %(levelname)s | %(funcName)s : %(message)s'
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

BG_COLOR = "#EFEFFA" #"#FCFFF3"
