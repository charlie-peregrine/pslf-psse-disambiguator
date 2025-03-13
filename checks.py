# checks.py, Charlie Jordan, 3/7/2025

import multiprocessing
from pathlib import Path
import subprocess
import sys
import threading
from contextlib import redirect_stdout
import io
import traceback
import logging
logger = logging.getLogger(__name__)

import consts
import files

CLOSE_THREAD = None

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
                slice_ = head[offset:offset+len(code)]
                eq = slice_ == code
                logger.info(f"{repr(slice_)} == {repr(code)} -> {eq}")
                if eq:
                    return program
    return ''

def history_check(file):
    history = files.load_history()
    if file in history:
        logger.info(f"File found in history: {file}")
        return history[file]
    else:
        logger.info(f"File not found in history: {file}")
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
        logger.error("==== open_check_pslf ERROR ====")
        map(logger.error, traceback.format_exc().split('\n'))
        logger.error("==== open_check_pslf ERROR END ====")
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
            logger.error("==== open_check_psse ERROR ====")
            map(logger.error, traceback.format_exc().split('\n'))
            logger.error("==== open_check_psse ERROR END ====")
    print("out:", out.getvalue())
    logger.info("PSSE output:")
    map(logger.info, out.getvalue().split('\n'))
    return psse_good

def open_check(file):
    configs = files.load_config()
    if configs is None:
        return ''
    q = multiprocessing.Queue()
    logger.info("Starting Process 1")
    p1 = multiprocessing.Process(target=open_check_pslf,
            args=(file, configs['pslf'], q), daemon=True)
    p1.start()
    logger.info("Starting Process 2")
    p2 = multiprocessing.Process(target=open_check_psse,
            args=(file, configs['psse'], q), daemon=True)
    p2.start()
    
    def join_processes(p1, p2):
        logger.info("Joining Process 1")
        p1.join()
        logger.info("Process 1 Joined")
        logger.info("Joining Process 2")
        p2.join()
        logger.info("Process 2 Joined")
    
    logger.info("Starting join processed thread")
    CLOSE_THREAD = threading.Thread(target=join_processes, args=(p1, p2))
    CLOSE_THREAD.start()

    logger.info("Waiting for queue")
    checked = 0
    result = ''
    while checked < 2:
        val = q.get()
        checked += 1
        if val:
            result = val
            break
    logger.info("Done waiting for queue")
    
    return result

def join_close_thread():
    if CLOSE_THREAD is not None:
        logger.info("Joining CLOSE_THREAD")
        CLOSE_THREAD.join()
        logger.info("CLOSE_THREAD joined")