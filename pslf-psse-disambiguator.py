# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import json
import subprocess
import sys
from pathlib import Path
import importlib.util
import time
from typing import Callable, Any
import multiprocessing
import threading
from contextlib import redirect_stderr, redirect_stdout
import io

PPD_DIR = Path(__file__).resolve().parent

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('> running in a PyInstaller bundle')
    IS_BUNDLED = True
    EXE_DIR = Path(sys.executable).resolve().parent
else:
    print('> running in a normal Python process')
    IS_BUNDLED = False
    EXE_DIR = PPD_DIR

# sys.executable is the location of the exe
print("> PPD_DIR:", PPD_DIR)
print("> EXE_DIR:", EXE_DIR)

DEFAULT_PSLF_DIR_PATH = Path(r"C:\Program Files\GE PSLF")
DEFAULT_PSSE_DIR_PATH = Path(r"C:\Program Files\PTI\PSSE35\35.6")

PSLF_EXE_SUFFIX = "Pslf.exe"
PSSE_EXE_SUFFIX = "PSSBIN/psse35.exe"
PSLF_PY_SUFFIX = "PslfPython/PSLF_PYTHON.py"
PSSE_PY_SUFFIX = "PSSPY311/psse35.py"

CONFIG_FILENAME = ".ppd-config.json"
HISTORY_FILENAME = ".history.json"

# the codes found at the start of the sav files. offset included
BYTE_HINTS = {
    'pslf' : (
        (0, b'SQLite format'),
        (8, b'Version'),
    ),
    'psse' : (
        (0, b'FuP_pHySPCD%'),
    )
}

CLOSE_THREAD = None

def is_valid_pslf_version(path):
    pass # use 'Pslf.exe --version' and checkoutput to see if version is greater than or equal to 23.1.0
    return True

def is_valid_psse_version(path):
    pass # read the first line from readme.txt in the toplevel psse_dir to get the version
        # and see if it's greater than or equal to 35.6.2 
    return True

def keep_asking(
    prompt: str = "(y/n) ",
    yes_test: str | Callable[[str], bool] = 'y',
    no_test: str | Callable[[str], bool] = 'n',
    yes_print: str | None = None,
    no_print: str | None = None,
    reprompt: str = "Enter y or n for yes or no"
):
    if isinstance(yes_test, str):
        yes_test_ = lambda x: x == yes_test
    else:
        yes_test_ = yes_test
    if isinstance(no_test, str):
        no_test_ = lambda x: x == no_test
    else:
        no_test_ = no_test
    while True:
        inp = input(prompt)
        if yes_test_(inp):
            if yes_print is not None:
                print(yes_print)
            return True
        elif no_test_(inp):
            if no_print is not None:
                print(no_print)
            return False
        else:
            print(reprompt)

def setup_():
    # ls = []
    # for p in sys.path:
    #     if "pslfpython" in p.lower() or "psspy" in p.lower():
    #         ls.append(p)
    # print(len(sys.path))
    # for p in ls:
    #     sys.path.remove(p)
    # print(len(sys.path))
    configs = load_config()
    if configs is None:
        pslf_dir_path = DEFAULT_PSLF_DIR_PATH
        psse_dir_path = DEFAULT_PSSE_DIR_PATH
        configs = {}
    else:
        pslf_dir_path = Path(configs['pslf'])
        psse_dir_path = Path(configs['psse'])
        

    print("Using the following directories to find pslf and psse executables.")
    print("If you have multiple versions of either program or installed them")
    print("somewhere different than the default location, you may need to change")
    print("these.")
    print("PSLF:", pslf_dir_path)
    print("PSSE:", psse_dir_path)
    keep_asking("Change these values? (y/n) ", yes_print="edit here (WIP)",
                no_print="Keeping")
    
    pslf_exe_path = pslf_dir_path / PSLF_EXE_SUFFIX
    psse_exe_path = psse_dir_path / PSSE_EXE_SUFFIX
    
    # @TODO check that the exe files exist
    # while not pslf_exe_path.exists():
    #     pass # ask for new directory
    # while not psse_exe_path.exists():
    #     pass # ask for new directory
    
    configs['pslf'] = str(pslf_dir_path)
    configs['psse'] = str(psse_dir_path)
    
    
    print("Skip the 'Pick a program' window when opening a sav file that has")
    print("been opened before? If you're not sure, then choose yes.")
    configs['skip_prompt'] = keep_asking(yes_print="always", no_print="only sometimes")

    pslf_py_path = pslf_dir_path / PSLF_PY_SUFFIX
    psse_py_path = psse_dir_path / PSSE_PY_SUFFIX
    
    # add paths to import search paths
    sys.path.append(str(pslf_py_path.parent))
    sys.path.append(str(psse_py_path.parent))
    
    use_python_libraries = True
    if not is_valid_pslf_version(psse_exe_path):
        use_python_libraries = False
        print("invalid pslf version for python libraries")
    elif importlib.util.find_spec('PSLF_PYTHON') is None:
        use_python_libraries = False
        print("Can't find pslf python")
    if not is_valid_psse_version(psse_dir_path):
        use_python_libraries = False
        print("invalid psse version for python libraries")
    elif importlib.util.find_spec('psse35') is None:
        use_python_libraries = False
        print("Can't find psse python")
    configs['use_python'] = use_python_libraries
    
    
    save_config(configs)
    if not load_history():
        save_history({})
    
    
    # set fta here
    if IS_BUNDLED:
        pass 
        # set_file_type_association(sys.executable, "psse.ico", ".sav")
    else:
        print("> skipping set fta for unbundled files")

def set_file_type_association(exe_path, icon_name, extension):
    exe_path = Path(exe_path).resolve()
    sfta_path = PPD_DIR / "PS-SFTA\\SFTA.ps1"
    ico_path = PPD_DIR / icon_name

    ps_command = f"""Register-FTA '{exe_path}' {extension} -Icon '{ico_path}'"""
    cmd_command = f"""powershell -ExecutionPolicy Bypass -command "& {{ . '{sfta_path}'; {ps_command} }}" """

    # print("Power shell SFTA string:")
    # print(cmd_command)

    p = subprocess.run(
        cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    print(p.stdout)
    return p.returncode
    # if p.returncode:
    #     print("File type association failed!")
    # else:
    #     print("File type association succeeded!")

def bytes_check(file):
    with open(file, 'rb') as fp:
        head = fp.read(32)
        for program, hints in BYTE_HINTS.items():
            for offset, code in hints:
                if head[offset:len(code)] == code:
                    return program
    return ''

def history_check(file):
    history = load_history()
    if file in history:
        return history[file]
    else:
        return ''

def open_check_pslf(file, prog_dir, queue_: multiprocessing.Queue):
    # add paths to import search paths
    pslf_py_path = Path(prog_dir) / PSLF_PY_SUFFIX
    sys.path.append(str(pslf_py_path.parent))
    
    pslf_good = False
    try:
        from PSLF_PYTHON import Pslf, PSLFInstance, exit_pslf
        path = Path(PSLF_EXE_SUFFIX).name
        args = [path, "-w", str(Path(file).parent), "-s"]
        popen_obj = subprocess.Popen(args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT) # Call subprocess
        PSLFInstance.instance = str(popen_obj.pid)

        # check here
        try:
            Pslf.load_case(file)
            pslf_good = True
        except Exception:
            pslf_good = False
        queue_.put('pslf' if pslf_good else '')
        
        exit_pslf()
        
    except Exception as e:
        import traceback
        traceback.print_exception(e)
    return pslf_good

def open_check_psse(file, prog_dir, queue_: multiprocessing.Queue):
    with redirect_stdout(io.StringIO()) as out:
        psse_py_path = Path(prog_dir) / PSSE_PY_SUFFIX
        sys.path.append(str(psse_py_path.parent))
        psse_good = True
        try:
            import psse35 # type: ignore
            import psspy # type: ignore
            psspy.psseinit()
            queue_.put('psse' if psspy.case(file) == 0 else '')
            psspy.pssehalt_2()
            
        except Exception as e:
            import traceback
            traceback.print_exception(e)
    # print("out:", out.getvalue())
    return psse_good


def open_check(file):
    configs = load_config()
    if configs is None:
        return ''
    q = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=open_check_pslf,
            args=(file, configs['pslf'], q), daemon=True)
    p1.start()
    p2 = multiprocessing.Process(target=open_check_psse,
            args=(file, configs['psse'], q), daemon=True)
    p2.start()
    
    def join_processes(p1, p2):
        p1.join()
        p2.join()
    
    CLOSE_THREAD = threading.Thread(target=join_processes, args=(p1, p2))
    CLOSE_THREAD.start()

    checked = 0
    result = ''
    while checked < 2:
        val = q.get()
        checked += 1
        if val:
            result = val
            break
    
    return result

def run_program(program, file):
    command_format = 'cd "{work_dir}" & "{exe}" "{file}"'
    work_dir = str(Path(file).parent)

    if program == 'pslf':
        suffix = PSLF_EXE_SUFFIX
    elif program == 'psse':
        suffix = PSSE_EXE_SUFFIX
    else:
        command_text = command_format.format(
            work_dir=work_dir, exe=program, file=file
        )
        print("Generic command text:", command_format)
        return subprocess.Popen(command_text, shell=True)

    config = load_config()
    if config is None:
        raise KeyError("Configuration file not found")
    exe = Path(config[program]) / suffix
    command_text = command_format.format(work_dir=work_dir, exe=exe, file=file)
    print(program + " command_text:", command_text)
    return subprocess.Popen(command_text, shell=True)

def save_config(config_dict):
    config_path = EXE_DIR / CONFIG_FILENAME
    # @TODO do some checks here for contents?
    with open(config_path, 'w') as fp:
        json.dump(config_dict, fp, indent=2)

def load_config():
    config_path = EXE_DIR / CONFIG_FILENAME
    try:
        with open(config_path, 'r') as fp:
            return json.load(fp)
    except FileNotFoundError:
        return None

def save_history(history_dict):
    history_path = EXE_DIR / HISTORY_FILENAME
    with open(history_path, 'w') as fp:
        json.dump(history_dict, fp, indent=2)

def load_history():
    history_path = EXE_DIR / HISTORY_FILENAME
    try:
        with open(history_path, 'r') as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {}

def history_set(file, program):
    history = load_history()
    history[file] = program
    save_history(history)
    

def main():
    # try loading config.json
    configs = load_config()

    # show setup window
    if configs is None or len(sys.argv) < 2:
        setup_()
        configs = load_config()
        assert configs is not None
    # do normal disambiguation
    if len(sys.argv) > 1:
        file = sys.argv[1]
        
        # open history and check if the file is there
        hist_prog = history_check(file)
        print(f"history_check result: '{hist_prog}'")
        if configs['skip_prompt'] and hist_prog:
            run_program(hist_prog, file)
            return
        
        bytes_prog = bytes_check(file)
        print(f"bytes_check result: '{bytes_prog}'")
        if configs['skip_prompt'] and bytes_prog:
            p = run_program(bytes_prog, file)
            history_set(file, bytes_prog)
            return

        open_prog = ''
        if configs['use_python']:
            open_prog = open_check(file)
            if configs['skip_prompt'] and open_prog:
                run_program(open_prog, file)
                return

        
        
        
        # open a window here showing the prompt
        # if user wants a different program open file dialog for C:\ProgramData\Microsoft\Windows\Start Menu\Programs
        
        print("prompt time")

if __name__ == '__main__':
    main()
    input("Press Enter to close")
    if CLOSE_THREAD is not None:
        CLOSE_THREAD.join()
