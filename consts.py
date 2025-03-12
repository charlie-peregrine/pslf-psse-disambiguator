# consts.py, Charlie Jordan, 3/7/2025

import sys
from pathlib import Path

PPD_DIR = Path(__file__).resolve().parent

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # print('> running in a PyInstaller bundle')
    IS_BUNDLED = True
    EXE_DIR = Path(sys.executable).resolve().parent
else:
    # print('> running in a normal Python process')
    IS_BUNDLED = False
    EXE_DIR = PPD_DIR

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

CLOSE_THREAD = None

BG_COLOR = "#EFEFFA" #"#FCFFF3"
