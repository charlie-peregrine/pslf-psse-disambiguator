# checks.py, Charlie Jordan, 3/7/2025

import multiprocessing
from pathlib import Path
import subprocess
import sys
import threading
from contextlib import redirect_stdout
import io

import consts
import files

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

def bytes_check(file):
    with open(file, 'rb') as fp:
        head = fp.read(32)
        for program, hints in BYTE_HINTS.items():
            for offset, code in hints:
                if head[offset:offset+len(code)] == code:
                    return program
    return ''

def history_check(file):
    history = files.load_history()
    if file in history:
        return history[file]
    else:
        return ''

def open_check_pslf(file, prog_dir, queue_: multiprocessing.Queue):
    # add paths to import search paths
    pslf_py_path = Path(prog_dir) / consts.PSLF_PY_SUFFIX
    sys.path.append(str(pslf_py_path.parent))
    
    pslf_good = False
    try:
        from PSLF_PYTHON import Pslf, PSLFInstance, exit_pslf
        path = Path(consts.PSLF_EXE_SUFFIX).name
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
        psse_py_path = Path(prog_dir) / consts.PSSE_PY_SUFFIX
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
    configs = files.load_config()
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
    
    consts.CLOSE_THREAD = threading.Thread(target=join_processes, args=(p1, p2))
    consts.CLOSE_THREAD.start()

    checked = 0
    result = ''
    while checked < 2:
        val = q.get()
        checked += 1
        if val:
            result = val
            break
    
    return result
