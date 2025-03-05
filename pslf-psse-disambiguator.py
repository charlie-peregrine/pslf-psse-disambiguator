# pslf-psse-disambiguator.py, Charlie Jordan, 3/5/2025

import json
import subprocess
import sys
from pathlib import Path
import importlib.util

PSLF_PATH = Path(r"C:\Program Files\GE PSLF\PslfPython\PSLF_PYTHON.py")
PSSE_PATH = Path(r"C:\Program Files\PTI\PSSE35\35.6\PSSPY311\psse35.py")

def setup_():
    # ls = []
    # for p in sys.path:
    #     if "pslfpython" in p.lower() or "psspy" in p.lower():
    #         ls.append(p)
    # print(len(sys.path))
    # for p in ls:
    #     sys.path.remove(p)
    # print(len(sys.path))
    
    # add paths to import search paths
    sys.path.append(str(PSLF_PATH.parent))
    sys.path.append(str(PSSE_PATH.parent))
    
    bad_news = 0
    if importlib.util.find_spec('PSLF_PYTHON') is None:
        bad_news += 1
        print("Can't find pslf")
    if importlib.util.find_spec('psse35') is None:
        bad_news += 1
        print("Can't find psse")
    if bad_news:
        return 1
    
    configs = {
        'pslf': str(PSLF_PATH),
        'psse': str(PSSE_PATH),
    }
    
    with open("config.json", 'w') as file:
        json.dump(configs, file, indent=2)
    
    # set fta here
    set_file_type_association("pslf-psse-disambiguator.exe", "psse.ico", ".rctj")

def set_file_type_association(exe_path, icon_name, extension):
    exe_path = Path(exe_path).resolve()
    sfta_path = Path("PS-SFTA\\SFTA.ps1").resolve()
    ico_path = Path(f"{icon_name}").resolve()

    ps_command = f"""Register-FTA '{exe_path}' {extension} -Icon '{ico_path}'"""
    cmd_command = f"""powershell -ExecutionPolicy Bypass -command "& {{ . '{sfta_path}'; {ps_command} }}" """

    # print("Power shell SFTA string:")
    # print(cmd_command)

    p = subprocess.run(
        cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    # print(p.stdout)
    return p.returncode
    # if p.returncode:
    #     print("File type association failed!")
    # else:
    #     print("File type association succeeded!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(sys.argv[1:])
        pass # do normal disambiguation
    else:
        setup_()
        pass # show setup window
    # print(sys.argv)
    # input()