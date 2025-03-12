# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import subprocess
import sys
from pathlib import Path
import multiprocessing

import consts
import checks
import files
from SetupWindow import SetupWindow


def run_program(program, file):
    command_format = 'cd "{work_dir}" & "{exe}" "{file}"'
    work_dir = str(Path(file).parent)

    if program == 'pslf':
        suffix = consts.PSLF_EXE_SUFFIX
    elif program == 'psse':
        suffix = consts.PSSE_EXE_SUFFIX
    else:
        command_text = command_format.format(
            work_dir=work_dir, exe=program, file=file
        )
        print("Generic command text:", command_format)
        return subprocess.Popen(command_text, shell=True)

    config = files.load_config()
    if config is None:
        raise KeyError("Configuration file not found")
    exe = Path(config[program]) / suffix
    command_text = command_format.format(work_dir=work_dir, exe=exe, file=file)
    print(program + " command_text:", command_text)
    return subprocess.Popen(command_text, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)


def main():
    # try loading config.json
    configs = files.load_config()

    # show setup window
    if configs is None or len(sys.argv) < 2:
        setupwindow = SetupWindow()
        setupwindow.mainloop()
        if not setupwindow.done:
            return
        configs = files.load_config()
        assert configs is not None
    # do normal disambiguation
    if len(sys.argv) > 1:
        file = sys.argv[1]
        print(sys.argv)
        import json
        json.dumps(configs, indent=2, default=files.path_default)
        # maybe add something here where if the user is holding down control
        # we disable skip prompt.
        
        # open history and check if the file is there
        hist_prog = checks.history_check(file)
        print(f"history_check result: '{hist_prog}'")
        if configs['skip_prompt'] and hist_prog:
            run_program(hist_prog, file)
            return
        
        # check the header bytes
        bytes_prog = checks.bytes_check(file)
        print(f"bytes_check result: '{bytes_prog}'")
        if configs['skip_prompt'] and bytes_prog:
            p = run_program(bytes_prog, file)
            files.history_set(file, bytes_prog)
            return

        # if this is the right version to use the python libraries then check
        # if the program can be run with those.
        open_prog = ''
        if configs['use_python']:
            open_prog = checks.open_check(file)
            print(f"open_check result: '{open_prog}'")
            if configs['skip_prompt'] and open_prog:
                run_program(open_prog, file)
                files.history_set(file, open_prog)
                return

        
        
        
        # open a window here showing the prompt
        # if user wants a different program open file dialog for C:\ProgramData\Microsoft\Windows\Start Menu\Programs
        
        print("prompt time")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
    # input("Press Enter to close")
    checks.join_close_thread()
