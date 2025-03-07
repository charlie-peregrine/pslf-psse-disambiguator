# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import subprocess
import sys
from pathlib import Path
import importlib.util
from typing import Callable
import multiprocessing

import consts
import checks
import files



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
    configs = files.load_config()
    if configs is None:
        pslf_dir_path = consts.DEFAULT_PSLF_DIR_PATH
        psse_dir_path = consts.DEFAULT_PSSE_DIR_PATH
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
    
    pslf_exe_path = pslf_dir_path / consts.PSLF_EXE_SUFFIX
    psse_exe_path = psse_dir_path / consts.PSSE_EXE_SUFFIX
    
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

    pslf_py_path = pslf_dir_path / consts.PSLF_PY_SUFFIX
    psse_py_path = psse_dir_path / consts.PSSE_PY_SUFFIX
    
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
    
    
    files.save_config(configs)
    if not files.load_history():
        files.save_history({})
    
    
    # set fta here
    if consts.IS_BUNDLED:
        pass 
        set_file_type_association(sys.executable, "ppd.ico", ".sav")
    else:
        print("> skipping set fta for unbundled files")

def set_file_type_association(exe_path, icon_name, extension):
    exe_path = Path(exe_path).resolve()
    sfta_path = consts.PPD_DIR / "PS-SFTA\\SFTA.ps1"
    ico_path = consts.PPD_DIR / icon_name

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
    return subprocess.Popen(command_text, shell=True)


def main():
    # try loading config.json
    configs = files.load_config()

    # show setup window
    if configs is None or len(sys.argv) < 2:
        setup_()
        configs = files.load_config()
        assert configs is not None
    # do normal disambiguation
    if len(sys.argv) > 1:
        file = sys.argv[1]
        print(sys.argv)
        
        # open history and check if the file is there
        hist_prog = checks.history_check(file)
        print(f"history_check result: '{hist_prog}'")
        if configs['skip_prompt'] and hist_prog:
            run_program(hist_prog, file)
            return
        
        bytes_prog = checks.bytes_check(file)
        print(f"bytes_check result: '{bytes_prog}'")
        if configs['skip_prompt'] and bytes_prog:
            p = run_program(bytes_prog, file)
            files.history_set(file, bytes_prog)
            return

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
    if consts.CLOSE_THREAD is not None:
        consts.CLOSE_THREAD.join()
